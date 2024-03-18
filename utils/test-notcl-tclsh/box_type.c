// SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
// SPDX-License-Identifier: Apache-2.0

#include <stdio.h>
#include <stdlib.h>
#include <tcl/tcl.h>

#include "box_type.h"

static int box_counter = 0; // potentially not thread-safe

static Tcl_ObjType BoxType = {
    "box",
    FreeBox, // Tcl_FreeInternalRepProc
    DupBox, // Tcl_DupInternalRepProc
    NULL, // Tcl_UpdateStringProc:
    NULL // Tcl_SetFromAnyProc: NULL, since we do not register our type
};

struct BoxCustomData {
    int box_int;
};


int Box_Init(Tcl_Interp *interp) {

    return TCL_OK;
}

Tcl_Obj *NewBox(int wrapped_value) {
    Tcl_Obj *obj;
    char str[100];

    struct BoxCustomData *data;

    fprintf(stderr, "log: NewBox called.\n");

    data = ckalloc(sizeof(struct BoxCustomData));
    data->box_int = wrapped_value;

    sprintf(str, "Box%i", box_counter++);

    obj = Tcl_NewStringObj(str, -1);
    obj->typePtr = &BoxType;
    obj->internalRep.twoPtrValue.ptr1 = data;

    return obj;
}

int UnwrapBox(Tcl_Obj *obj, int *box_int) {
    struct BoxCustomData *data;

    if(obj->typePtr != &BoxType) {
        return TCL_ERROR;
    }

    data = obj->internalRep.twoPtrValue.ptr1;
    
    *box_int = data->box_int;

    return TCL_OK;
}

void FreeBox(Tcl_Obj *obj) {
    struct BoxCustomData *data;

    fprintf(stderr, "log: FreeBox called.\n");

    if(obj->typePtr != &BoxType) {
        return;
    }

    data = obj->internalRep.twoPtrValue.ptr1;

    ckfree(data);
}

void DupBox(Tcl_Obj *srcPtr, Tcl_Obj *dupPtr) {
    fprintf(stderr, "log: DupBox called.\n");
    // I am not sure whether this function will ever be called,
    // since we do not register our ObjType with Tcl.
}