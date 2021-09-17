use std::time::{Duration, SystemTime};
use std::io::{self, Write, Read};
use std::process;
use serialport::TTYPort;

fn main() {
    let mut port = serialport::new("/dev/ttyUSB2", 115_200)
        .timeout(Duration::from_millis(10))
        .open_native().expect("Failed to open port.");

    port.set_exclusive(true).expect("Failed to get exclusive access to port");

    port.write_all("ATI\r\n".as_bytes()).expect("Write failed");

    let start_time = SystemTime::now();
    let mut response = Vec::new();
    loop {
        match start_time.elapsed() {
            Ok(elapsed) if elapsed > Duration::from_millis(500) =>
                return print_buffer(&response),
            Ok(_) => (),
            Err(_) => ()
        }

        let mut buff = [0; 64];
        match port.read(&mut buff) {
            Ok(len) => response.extend_from_slice(&buff[0..len]),
            Err(ref e) if e.kind() == io::ErrorKind::TimedOut => (),
            Err(e) => {
                eprintln!("Error while reading: {:?}", e);
                process::exit(1)
            }
        }
    }
}

fn execute_command(port : &mut TTYPort, cmd : &String, wait : Duration) -> Result<String> {

}

fn print_buffer(buff : &Vec<u8>) -> () {
    io::stdout().write_all(&buff.as_slice()).expect("Failed to write to stdout")
}