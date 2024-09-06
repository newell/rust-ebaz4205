all: ../build/firmware/armv7-none-eabihf/release/firmware ../build/firmware.bin

.PHONY: all

# ../build/pl.rs: gateware/*
# 	mkdir -p ../build
# 	python gateware/rust-pitaya.py -r ../build/pl.rs

../build/firmware/armv7-none-eabihf/release/firmware: $(shell find . -print)
	XBUILD_SYSROOT_PATH=`pwd`/../build/sysroot cargo xbuild --release -p firmware --target-dir ../build/firmware

../build/firmware.bin: ../build/firmware/armv7-none-eabihf/release/firmware
	llvm-objcopy -O binary ../build/firmware/armv7-none-eabihf/release/firmware ../build/firmware.bin
