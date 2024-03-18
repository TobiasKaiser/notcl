// SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
// SPDX-License-Identifier: Apache-2.0

#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <tcl/tcl.h>

#include "box_type.h"
#include "cmds_box.h"
#include "cmd_invert_case.h"
#include "cmd_infinite_loop.h"
#include "cmd_multiply.h"
#include "cmds_signal.h"

int cmd_ignore_sigint(ClientData cd, Tcl_Interp *interp, int objc, Tcl_Obj *CONST objv[]);
int cmd_reset_sigint(ClientData cd, Tcl_Interp *interp, int objc, Tcl_Obj *CONST objv[]);

static int my_appinit(Tcl_Interp *interp) {
    if(Tcl_Init(interp)) { 
        return TCL_ERROR;
    }
    if(Box_Init(interp)) {
        return TCL_ERROR;
    }

    // Tcl_SetVar(interp,"tcl_rcFileName","~/.wishrc",TCL_GLOBAL_ONLY);

    Tcl_CreateObjCommand(interp, "test_multiply", cmd_multiply, NULL, NULL);
    Tcl_CreateObjCommand(interp, "test_invert_case", cmd_invert_case, NULL, NULL);
    Tcl_CreateObjCommand(interp, "test_infinite_loop", cmd_infinite_loop, NULL, NULL);

    Tcl_CreateObjCommand(interp, "ignore_sigint", cmd_ignore_sigint, NULL, NULL);
    Tcl_CreateObjCommand(interp, "reset_sigint", cmd_reset_sigint, NULL, NULL);

    Tcl_CreateObjCommand(interp, "test_infinite_loop", cmd_infinite_loop, NULL, NULL);


    Tcl_CreateObjCommand(interp, "create_box", cmd_create_box, NULL, NULL);
    Tcl_CreateObjCommand(interp, "unwrap_box", cmd_unwrap_box, NULL, NULL);

    return TCL_OK;
}


int main(int argc, char *argv[]) {

    Tcl_Main(argc, argv, my_appinit);

    return 0; 
}