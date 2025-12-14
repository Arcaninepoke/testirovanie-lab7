#!/bin/bash

IMAGE=$(find ./romulus -name "*.static.mtd")

qemu-system-arm -m 256 -M romulus-bmc \
-nographic -drive file=$IMAGE,format=raw,if=mtd \
-net nic -net user,hostfwd=:0.0.0.0:2222-:22,hostfwd=:0.0.0.0:2443-:443,hostfwd=udp:0.0.0.0:2623-:623,hostname=qemu
