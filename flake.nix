{
  description = "Minimalist bare metal Rust firmware for EBAZ4205";

  inputs.artiq-zynq.url = git+https://git.m-labs.hk/m-labs/artiq-zynq;

  outputs = { self, artiq-zynq }:
    let
      pkgs = import artiq-zynq.inputs.artiq.inputs.nixpkgs { system = "x86_64-linux"; overlays = [ (import artiq-zynq.inputs.mozilla-overlay) ]; };
      zynqpkgs = artiq-zynq.inputs.zynq-rs.packages.x86_64-linux;
      artiqpkgs = artiq-zynq.inputs.artiq.packages.x86_64-linux;
      artiqzynqpkgs = artiq-zynq.packages.x86_64-linux;
      rustPlatform = artiq-zynq.inputs.zynq-rs.rustPlatform;
    in rec {
      packages.x86_64-linux = rec {
        rust-ebaz4205-firmware = rustPlatform.buildRustPackage {
          name = "rust-ebaz4205-firmware";

          src = ./src;
          cargoLock = {
            lockFile = src/Cargo.lock;
            outputHashes = {
              "libasync-0.0.0" = "sha256-gXML1pez4LvYxuAG9AX3inKq0e7+D8SvNd/tW4OwXu4=";
            };
          };

          nativeBuildInputs = [
            pkgs.gnumake
            (pkgs.python3.withPackages(ps: [ artiqpkgs.migen artiqpkgs.misoc artiqzynqpkgs.migen-axi ]))
            pkgs.cargo-xbuild
            pkgs.llvmPackages_9.llvm
            pkgs.llvmPackages_9.clang-unwrapped
          ];
          buildPhase = ''
            XARGO_RUST_SRC="${rustPlatform.rust.rustc}/lib/rustlib/src/rust/library";
            export CARGO_HOME=$(mktemp -d cargo-home.XXX)
            make
          '';

          installPhase = ''
            mkdir -p $out $out/nix-support
            cp ../build/firmware.bin $out/firmware.bin
            cp ../build/firmware/armv7-none-eabihf/release/firmware $out/firmware.elf
            echo file binary-dist $out/firmware.bin >> $out/nix-support/hydra-build-products
            echo file binary-dist $out/firmware.elf >> $out/nix-support/hydra-build-products
          '';

          doCheck = false;
          dontFixup = true;
        };
        rust-ebaz4205-gateware = pkgs.runCommand "rust-ebaz4205-gateware"
          {
            nativeBuildInputs = [
              (pkgs.python3.withPackages(ps: [ artiqpkgs.migen artiqpkgs.misoc artiqzynqpkgs.migen-axi ]))
              artiqpkgs.vivado
            ];
          }
          ''
          python ${./src/gateware}/ebaz4205.py -g build
          mkdir -p $out $out/nix-support
          cp build/top.bit $out
          echo file binary-dist $out/top.bit >> $out/nix-support/hydra-build-products
          '';
        rust-ebaz4205-jtag = pkgs.runCommand "rust-ebaz4205-jtag" {}
          ''
          mkdir $out
          ln -s ${zynqpkgs.szl}/szl-ebaz4205.elf $out
          ln -s ${rust-ebaz4205-firmware}/firmware.bin $out
          ln -s ${rust-ebaz4205-gateware}/top.bit $out
          '';
        rust-ebaz4205-sd = pkgs.runCommand "rust-ebaz4205-sd"
          {
            buildInputs = [ zynqpkgs.mkbootimage ];
          }
          ''
          # Do not use "long" paths in boot.bif, because embedded developers
          # can't write software (mkbootimage will segfault).
          bifdir=`mktemp -d`
          cd $bifdir
          ln -s ${zynqpkgs.szl}/szl-ebaz4205.elf szl.elf
          ln -s ${rust-ebaz4205-firmware}/firmware.elf firmware.elf
          ln -s ${rust-ebaz4205-gateware}/top.bit top.bit
          cat > boot.bif << EOF
          the_ROM_image:
          {
            [bootloader]szl.elf
            top.bit
            firmware.elf
          }
          EOF
          mkdir $out $out/nix-support
          mkbootimage boot.bif $out/boot.bin
          echo file binary-dist $out/boot.bin >> $out/nix-support/hydra-build-products
          '';
      };
      hydraJobs = packages.x86_64-linux;
      devShell.x86_64-linux = pkgs.mkShell {
        name = "rust-ebaz4205-dev-shell";
        buildInputs = with pkgs; [
          pkgs.gnumake
          rustPlatform.rust.rustc
          rustPlatform.rust.cargo
          pkgs.llvmPackages_9.llvm
          pkgs.llvmPackages_9.clang-unwrapped
          pkgs.cacert
          cargo-xbuild

          pkgs.openocd
          pkgs.openssh pkgs.rsync
          (pkgs.python3.withPackages(ps: [ artiqpkgs.migen artiqpkgs.misoc artiqzynqpkgs.migen-axi artiqzynqpkgs.artiq-netboot ]))
          artiqpkgs.vivado

          zynqpkgs.mkbootimage
        ];
        XARGO_RUST_SRC = "${rustPlatform.rust.rustc}/lib/rustlib/src/rust/library";
        OPENOCD_ZYNQ = "${artiq-zynq.inputs.zynq-rs}/openocd";
        SZL = "${zynqpkgs.szl}";
      };
    };
}
