// SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
// SPDX-License-Identifier: Apache-2.0

#include <stdio.h>
#include <stdlib.h>
#include <tcl/tcl.h>

#include "box_type.h"

int cmd_create_box(ClientData cd, Tcl_Interp *interp, int objc, Tcl_Obj *CONST objv[]) {
    Tcl_Obj *result;

    int box_int;

    if(objc!=2) {
        Tcl_WrongNumArgs(interp, 1, objv, "int");
        return TCL_ERROR;
    }
    
    if(Tcl_GetIntFromObj(interp,objv[1],&box_int)) {
        return TCL_ERROR;
    }

    result = NewBox(box_int);
    Tcl_SetObjResult(interp, result);

    return TCL_OK;
}

int cmd_unwrap_box(ClientData cd, Tcl_Interp *interp, int objc, Tcl_Obj *CONST objv[]) {
    Tcl_Obj *result;

    int box_int;

    if(objc!=2) {
        Tcl_WrongNumArgs(interp, 1, objv, "int");
        return TCL_ERROR;
    }
    
    if(UnwrapBox(objv[1], &box_int)) {
        result = Tcl_NewStringObj("object is not a box", -1);
        Tcl_SetObjResult(interp, result);

        return TCL_ERROR;
    }

    result = Tcl_NewIntObj(box_int);
    Tcl_SetObjResult(interp, result);

    return TCL_OK;
}
