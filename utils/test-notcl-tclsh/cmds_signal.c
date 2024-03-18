// SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
// SPDX-License-Identifier: Apache-2.0

#include <signal.h>
#include <tcl/tcl.h>

void intHandler(int dummy) {
    printf("\ngot ctrl+c\n");
}

int cmd_ignore_sigint(ClientData cd, Tcl_Interp *interp, int objc, Tcl_Obj *CONST objv[]) {
    Tcl_Obj *result;

    signal(SIGINT, intHandler);

    result = Tcl_NewIntObj(0);
    Tcl_SetObjResult(interp, result);

    return TCL_OK;
}

int cmd_reset_sigint(ClientData cd, Tcl_Interp *interp, int objc, Tcl_Obj *CONST objv[]) {
    Tcl_Obj *result;

    signal(SIGINT, SIG_DFL);

    result = Tcl_NewIntObj(0);
    Tcl_SetObjResult(interp, result);

    return TCL_OK;
}
