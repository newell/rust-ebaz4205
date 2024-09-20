#![no_std]
#![no_main]

extern crate alloc;

use log::{info, warn};
use alloc::{vec, format};

use libcortex_a9::asm;
use libboard_zynq::{
    eth::Eth,
    smoltcp::{
        self,
        iface::{EthernetInterfaceBuilder, NeighborCache},
        time::Instant,
        wire::IpCidr,
    },
    timer::GlobalTimer,
    logger,
    slcr
};
use libconfig::{net_settings, Config};
use libsupport_zynq::ram;
use libregister::RegisterW;

// #[path = "../../../build/pl.rs"]
// mod pl;

fn init_gateware() {
    // Set up PS->PL clocks
    slcr::RegisterBlock::unlocked(|slcr| {
        // As we are touching the mux, the clock may glitch, so reset the PL.
        slcr.fpga_rst_ctrl.write(
            slcr::FpgaRstCtrl::zeroed()
                .fpga0_out_rst(true)
                .fpga1_out_rst(true)
                .fpga2_out_rst(true)
                .fpga3_out_rst(true)
        );
        slcr.fpga0_clk_ctrl.write(
            slcr::Fpga0ClkCtrl::zeroed()
                .src_sel(slcr::PllSource::IoPll)
                .divisor0(8)
                .divisor1(1)
        );
        slcr.fpga_rst_ctrl.write(
            slcr::FpgaRstCtrl::zeroed()
        );
    });
}

// fn identifier_read(buf: &mut [u8]) -> &str {
//     unsafe {
//         pl::csr::identifier::address_write(0);
//         let len = pl::csr::identifier::data_read();
//         let len = cmp::min(len, buf.len() as u8);
//         for i in 0..len {
//             pl::csr::identifier::address_write(1 + i);
//             buf[i as usize] = pl::csr::identifier::data_read();
//         }
//         str::from_utf8_unchecked(&buf[..len as usize])
//     }
// }

#[derive(PartialEq)]
enum State {
    Idle,
    SendingMessage
}

#[no_mangle]
pub fn main_core0() {
    GlobalTimer::start();
    logger::init().unwrap();
    log::set_max_level(log::LevelFilter::Info);

    info!("EBAZ4205 firmware starting...");

    ram::init_alloc_core0();

    init_gateware();
    // info!("detected gateware: {}", identifier_read(&mut [0; 64]));

    let cfg = match Config::new() {
        Ok(cfg) => cfg,
        Err(err) => {
            warn!("config initialization failed: {}", err);
            Config::new_dummy()
        }
    };

    let net_addresses = net_settings::get_addresses(&cfg);
    log::info!("Network addresses: {}", net_addresses);
    let eth = Eth::eth0(net_addresses.hardware_addr.0.clone());
    let eth = eth.start_rx(8);
    let mut eth = eth.start_tx(8);

    let mut neighbor_map = [None; 2];
    let neighbor_cache = NeighborCache::new(&mut neighbor_map[..]);
    let mut ip_addrs = [IpCidr::new(net_addresses.ipv4_addr, 0)];
    let mut interface = EthernetInterfaceBuilder::new(&mut eth)
        .ethernet_addr(net_addresses.hardware_addr)
        .ip_addrs(&mut ip_addrs[..])
        .neighbor_cache(neighbor_cache)
        .finalize();

    let mut rx_storage = vec![0; 64];
    let mut tx_storage = vec![0; 4096];

    let mut socket_set_entries: [_; 1] = Default::default();
    let mut sockets = smoltcp::socket::SocketSet::new(&mut socket_set_entries[..]);

    let tcp_rx_buffer = smoltcp::socket::TcpSocketBuffer::new(&mut rx_storage[..]);
    let tcp_tx_buffer = smoltcp::socket::TcpSocketBuffer::new(&mut tx_storage[..]);
    let tcp_socket = smoltcp::socket::TcpSocket::new(tcp_rx_buffer, tcp_tx_buffer);
    let tcp_handle = sockets.add(tcp_socket);

    let timer = unsafe { GlobalTimer::get() };
    let mut state = State::Idle;

    log::info!("Waiting for connections...");
    loop {
        let timestamp = Instant::from_millis(timer.get_time().0 as i64);
        let message = format!("Hello! Current timestamp: {:?}", timestamp);

        log::info!("{}", message);

        {
            let socket = &mut *sockets.get::<smoltcp::socket::TcpSocket>(tcp_handle);

            if !socket.is_open() {
                socket.listen(1550).unwrap();
            }

            if socket.may_recv() {
                let start_cmd = socket.recv(|data| (data.len(), data.len() > 0)).unwrap();
                if start_cmd && state == State::Idle {
                    log::info!("Sending hello message");
                    state = State::SendingMessage;
                }
            } else if socket.may_send() {
                log::info!("disconnected");
                state = State::Idle;
                socket.close();
            }

            if state == State::SendingMessage {
                match socket.send_slice(message.as_bytes()) {
                    Ok(_) => {
                        log::info!("Message sent: {}", message);
                        state = State::Idle;
                    }
                    Err(e) => {
                        log::error!("Error while transmitting: {}", e);
                        state = State::Idle;
                        socket.close();
                    }
                }
            }
        }

        match interface.poll(&mut sockets, timestamp) {
            Ok(_) => (),
            Err(smoltcp::Error::Unrecognized) => (),
            Err(err) => log::error!("Network error: {}", err),
        }
    }
}

#[no_mangle]
pub fn main_core1() {
    loop {
        asm::wfe();
    }
}

// // BLINKY LED FIRMWARE
// #![no_std]
// #![no_main]

// use log::info;

// use libcortex_a9::asm;
// use libboard_zynq::{
//     timer::GlobalTimer,
//     logger
// };
// use libsupport_zynq::ram;

// pub mod led;
// use led::LED;

// #[no_mangle]
// pub fn main_core0() {
//     GlobalTimer::start();
//     logger::init().unwrap();
//     log::set_max_level(log::LevelFilter::Info);

//     info!("Rust EBAZ4205 firmware starting...");

//     ram::init_alloc_core0();

//     // init_gateware();
//     // info!("detected gateware: {}", identifier_read(&mut [0; 64]));

//     let timer = unsafe { GlobalTimer::get() };

//     let mut led = LED::new();

//     log::info!("Start blinking LEDs...");
//     let mut led_state = false;

//     loop {
//         let current_time = timer.get_time().0;

//         log::info!("LED state toggled at time: {}", current_time);

//         // Toggle LED state
//         led.toggle(led_state);
//         led_state = !led_state; // Invert state for the next toggle


//         for _ in 0..100_000_000 {
//             asm::nop();
//         }
//     }
// }

// #[no_mangle]
// pub fn main_core1() {
//     loop {
//         asm::wfe();
//     }
// }
