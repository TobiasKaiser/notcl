// SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
// SPDX-License-Identifier: Apache-2.0

#include <stdio.h>
#include <stdlib.h>
#include <tcl/tcl.h>

int cmd_invert_case(ClientData cd, Tcl_Interp *interp, int objc, Tcl_Obj *CONST objv[]) {
    Tcl_Obj *result;

    char *str_in, *str_out;
    int str_length, i;

    if(objc!=2) {
        Tcl_WrongNumArgs(interp, 1, objv, "str");
        return TCL_ERROR;
    }
    
    if(!(str_in=Tcl_GetStringFromObj(objv[1], &str_length))) {
        return TCL_ERROR;
    }

    // Warning: std_out is not null-terminated (and does not need to be).
    str_out = alloca(str_length * sizeof(char));

    if(!str_out) {
        perror("alloca failed");
        return TCL_ERROR;
    }

    for(i=0;i<str_length;i++) {
        char c = str_in[i];
        char c_out;
        if(c>='a' && c<='z') {
            c_out = c - 'a' + 'A';
        } else if(c>='A' && c <='Z') {
            c_out = c - 'A' + 'a';
        } else {
            c_out = c;
        }
        str_out[i] = c_out;
    }

    result = Tcl_NewStringObj(str_out, str_length);
    Tcl_SetObjResult(interp, result);

    return TCL_OK;
}