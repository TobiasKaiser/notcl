int Box_Init(Tcl_Interp *interp);

Tcl_Obj *NewBox(int wrapped_value);
int UnwrapBox(Tcl_Obj *obj, int *box_int);

void FreeBox(Tcl_Obj *obj);
void DupBox(Tcl_Obj *srcPtr, Tcl_Obj *dupPtr);