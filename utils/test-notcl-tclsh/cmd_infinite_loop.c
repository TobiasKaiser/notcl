// SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
// SPDX-License-Identifier: Apache-2.0

#include <tcl/tcl.h>

int cmd_infinite_loop(ClientData cd, Tcl_Interp *interp, int objc, Tcl_Obj *CONST objv[]) {
    Tcl_Obj *result;

    while(1) {
        // infinite loop
    }

    result = Tcl_NewIntObj(123);
    Tcl_SetObjResult(interp, result);

    // This is equivalent to the two lines above:
    //result = Tcl_GetObjResult(interp);
    //Tcl_SetIntObj(result, product);

    return TCL_OK;
}
