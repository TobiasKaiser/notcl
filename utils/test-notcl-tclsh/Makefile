# SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

LIBS=-ltcl
SRCS=main.c cmd_multiply.c cmd_invert_case.c box_type.c cmds_box.c cmd_infinite_loop.c cmds_signal.c
CFLAGS=-Wall -Werror -Wfatal-errors

test-notcl-tclsh: $(SRCS)
	gcc $(CFLAGS) -o $@ $^ $(LIBS)