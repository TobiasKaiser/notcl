// SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
// SPDX-License-Identifier: Apache-2.0

#include <tcl/tcl.h>

int cmd_multiply(ClientData cd, Tcl_Interp *interp, int objc, Tcl_Obj *CONST objv[]) {
    Tcl_Obj *result;
    int a, b, product; 
    if(objc!=3) {
        Tcl_WrongNumArgs(interp, 1, objv, "int int");
        return TCL_ERROR;
    }

    if(Tcl_GetIntFromObj(interp,objv[1],&a)) {
        return TCL_ERROR;
    }

    if(Tcl_GetIntFromObj(interp,objv[2],&b)) {
        return TCL_ERROR;
    }

    product = a * b;
    
    result = Tcl_NewIntObj(product);
    Tcl_SetObjResult(interp, result);

    // This is equivalent to the two lines above:
    //result = Tcl_GetObjResult(interp);
    //Tcl_SetIntObj(result, product);

    return TCL_OK;
}
