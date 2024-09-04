Rust EBAZ4205
=============

Minimalist bare metal Rust firmware for EBAZ4205.

Development instructions
------------------------

TODO

<!-- Pure build with Nix and execution on a remote JTAG server:

```shell
nix build .#rust-ebaz4205-jtag
./remote_run.sh
```

Impure incremental build and execution on a remote JTAG server:

```shell
nix develop
cd src
gateware/ebaz4205.py -g ../build/gateware  # build gateware
make                                          # build firmware
cd ..
./remote_run.sh -i
```

Notes:

- The impure build process is also compatible with non-Nix systems.
- If the board is connected to the local machine, use the ``local_run.sh`` script.
- Due to questionable Zynq design decisions, JTAG boot works only once per power cycle.
  A good workaround is to power the Red Pitaya through a uhubctl-compatible USB hub and
  boot with a command such as:
  ``ssh rpi-3.m-labs.hk "uhubctl -a off -p 4; sleep 2; uhubctl -a on -p 4; sleep 2" && ./remote_run.sh -i``

-->

License
-------

Copyright (C) 2024 Newell Jensen.

Rust EBAZ4205 is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Rust EBAZ4205 is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with Rust Pitaya.  If not, see <http://www.gnu.org/licenses/>.
