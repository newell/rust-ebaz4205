#![no_std]
#![no_main]

extern crate alloc;

// use core::{cmp, str};
use log::info;
// use alloc::vec;

use libcortex_a9::asm;
use libboard_zynq::{
    timer::GlobalTimer,
    // error_led,
    logger
    // slcr
};
use libsupport_zynq::ram;

pub mod led;
use led::LED;

// #[path = "../../../build/pl.rs"]
// mod pl;

// fn init_gateware() {
//     // Set up PS->PL clocks
//     slcr::RegisterBlock::unlocked(|slcr| {
//         // As we are touching the mux, the clock may glitch, so reset the PL.
//         slcr.fpga_rst_ctrl.write(
//             slcr::FpgaRstCtrl::zeroed()
//                 .fpga0_out_rst(true)
//                 .fpga1_out_rst(true)
//                 .fpga2_out_rst(true)
//                 .fpga3_out_rst(true)
//         );
//         slcr.fpga0_clk_ctrl.write(
//             slcr::Fpga0ClkCtrl::zeroed()
//                 .src_sel(slcr::PllSource::IoPll)
//                 .divisor0(8)
//                 .divisor1(1)
//         );
//         slcr.fpga_rst_ctrl.write(
//             slcr::FpgaRstCtrl::zeroed()
//         );
//     });
// }

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

#[no_mangle]
pub fn main_core0() {
    GlobalTimer::start();
    logger::init().unwrap();
    log::set_max_level(log::LevelFilter::Info);

    info!("Rust EBAZ4205 firmware starting...");

    ram::init_alloc_core0();

    // init_gateware();
    // info!("detected gateware: {}", identifier_read(&mut [0; 64]));

    let timer = unsafe { GlobalTimer::get() };

    let mut led = LED::new();

    log::info!("Start blinking LEDs...");
    let mut led_state = false;

    loop {
        let current_time = timer.get_time().0;

        log::info!("LED state toggled at time: {}", current_time);

        // Toggle LED state
        led.toggle(led_state);
        led_state = !led_state; // Invert state for the next toggle


        for _ in 0..100_000_000 {
            asm::nop();
        }
    }
}

#[no_mangle]
pub fn main_core1() {
    loop {
        asm::wfe();
    }
}
