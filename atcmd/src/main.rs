use std::time::{Duration, SystemTime};
use std::io::{self, Write, Read, Error};
use std::process;
use serialport::TTYPort;
use std::str;
use std::string::FromUtf8Error;
use std::fmt::{Display, Formatter};

use lazy_static::lazy_static;
use regex::Regex;
use std::str::Utf8Error;
use clap::{AppSettings, Clap, crate_version};

#[derive(Clap)]
#[clap(version = crate_version!())]
#[clap(setting = AppSettings::ColoredHelp)]
struct Args {
    /// The modem device to execute the commands on
    #[clap(long)]
    device : String,

    /// Maximum duration to wait for each command result
    #[clap(long)]
    timeout_ms : Option<u16>,

    /// AT commands to execute
    #[clap(long)]
    cmds: Vec<String>
}

fn main() {
    let args : Args = Args::parse();

    let mut port =
        serialport::new(args.device, 115_200)
        .timeout(Duration::from_millis(10))
        .open_native().expect("Failed to open port.");

    for cmd in args.cmds {
        println!("{}", &cmd);
        match execute_command(&mut port, &cmd, Duration::from_millis(args.timeout_ms.unwrap_or(500) as u64)) {
            Ok(lines) => {
                for (i, line) in lines.iter().enumerate() {
                    println!("{}: {}", i, line);
                }
            },
            Err(e) => {
                eprint!("Failed while executing command: {}", e);
                process::exit(1);
            }
        }
    }
}

enum AtErr {
    IO(Error),
    FromUtf8(FromUtf8Error),
    Utf8(Utf8Error)
}

impl From<Error> for AtErr {
    fn from(err: Error) -> Self {
        AtErr::IO(err)
    }
}

impl From<FromUtf8Error> for AtErr {
    fn from(err: FromUtf8Error) -> Self {
        AtErr::FromUtf8(err)
    }
}

impl From<Utf8Error> for AtErr {
    fn from(err: Utf8Error) -> Self {
        AtErr::Utf8(err)
    }
}

impl Display for AtErr {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            AtErr::IO(e) => e.fmt(f),
            AtErr::FromUtf8(e) => e.fmt(f),
            AtErr::Utf8(e) => e.fmt(f)
        }
    }
}

fn execute_command(port : &mut TTYPort, cmd : &str, wait : Duration) -> Result<Vec<String>, AtErr> {
    port.write_all(cmd.as_bytes())?;
    port.write_all(b"\r\n")?;

    let start_time = SystemTime::now();
    let mut accumulator = LineParser::new();

    loop {
        match start_time.elapsed() {
            Ok(elapsed) if elapsed > wait => return Ok(accumulator.final_lines()?),
            _ => ()
        }

        let mut buff = [0; 32];
        match port.read(&mut buff) {
            Ok(len) => accumulator.put_bytes(&buff[0..len])?,
            Err(ref e) if e.kind() == io::ErrorKind::TimedOut => (),
            Err(e) => return Err(AtErr::IO(e))
        }

        if accumulator.has_error() || accumulator.has_ok() {
            return Ok(accumulator.final_lines()?)
        }
    }
}

struct LineParser {
    has_error : bool,
    has_ok : bool,
    lines : Vec<String>,
    line_acc : Vec<u8>
}

impl LineParser {
    fn new() -> LineParser {
        LineParser {
            has_error : false,
            has_ok : false,
            lines : vec! [],
            line_acc : vec! []
        }
    }

    fn put_bytes(&mut self, bytes : &[u8]) -> Result<(), AtErr> {
        for b in bytes {
            match *b {
                b'\r' => (),
                b'\n' => self.process_line()?,
                x => self.line_acc.push(x)
            }
        }

        Ok(())
    }

    fn process_line(&mut self) -> Result<(), AtErr> {
        lazy_static! {
            static ref OK_PATTERN : Regex = Regex::new(r"(?i)^\s+OK\s+$").unwrap();
            static ref ERROR_PATTERN : Regex = Regex::new(r"(?i)^\s+ERROR\s+$").unwrap();
        }

        let s = String::from(str::from_utf8(&self.line_acc.as_slice())?);
        self.line_acc.clear();

        self.has_ok = self.has_ok || OK_PATTERN.is_match(s.as_str());
        self.has_error = self.has_error || ERROR_PATTERN.is_match(s.as_str());

        self.lines.push(s);

        Ok(())
    }

    fn final_lines(mut self) -> Result<Vec<String>, AtErr> {
        if self.line_acc.len() > 0 {
            self.process_line()?;
        }

        Ok(self.lines)
    }

    fn has_error(&self) -> bool {
        self.has_error
    }

    fn has_ok(&self) -> bool {
        self.has_ok
    }
}