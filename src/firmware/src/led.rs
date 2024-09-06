use libregister::RegisterRW;
use libregister::{register, register_at, register_bit, register_bits};

pub struct LED {
    regs: RegisterBlock,
}

impl LED {
    pub fn new() -> Self {
        // No SLCR configuration needed for EMIO pins

        Self::initialize(0xFFFF - 0x0080)
    }

    fn initialize(gpio_output_mask: u16) -> Self {
        // Setup register block
        let self_ = Self {
            regs: RegisterBlock::new(),
        };

        // Setup GPIO output mask
        self_.regs.gpio_output_mask.modify(|_, w| {
            w.mask(gpio_output_mask)
        });

        self_.regs.gpio_direction.modify(|_, w| {
            w.lederr(true)
        });

        self_
    }

    pub fn toggle(&mut self, state: bool) {
        self.led_o(state);
        self.led_oe(state);
    }

    fn led_oe(&mut self, oe: bool) {
        self.regs.gpio_output_enable.modify(|_, w| {
             w.lederr(oe)
        })
    }

    fn led_o(&mut self, o: bool) {
        self.regs.gpio_output_mask.modify(|_, w| {
             w.lederr_o(o)
        })
    }
}

pub struct RegisterBlock {
    pub gpio_output_mask: &'static mut GPIOOutputMask,
    pub gpio_direction: &'static mut GPIODirection,
    pub gpio_output_enable: &'static mut GPIOOutputEnable,
}

impl RegisterBlock {
    pub fn new() -> Self {
        Self {
            gpio_output_mask: GPIOOutputMask::new(),
            gpio_direction: GPIODirection::new(),
            gpio_output_enable: GPIOOutputEnable::new(),
        }
    }
}

register!(gpio_output_mask, GPIOOutputMask, RW, u32);
register_at!(GPIOOutputMask, 0xE000A010, new);
register_bit!(gpio_output_mask, lederr_o, 0);
register_bits!(gpio_output_mask, mask, u16, 0, 15);

register!(gpio_direction, GPIODirection, RW, u32);
register_at!(GPIODirection, 0xE000A284, new);
register_bit!(gpio_direction, lederr, 0);

register!(gpio_output_enable, GPIOOutputEnable, RW, u32);
register_at!(GPIOOutputEnable, 0xE000A288, new);
register_bit!(gpio_output_enable, lederr, 0);
