# base64::encode and base64::decode are used instead of "binary encode base64"
# and "binary decode base64" for Tcl 8.5 (?) support.
namespace eval NoTcl {
    global env

    set fn_tcl2py $env(NOTCL_PIPE_TCL2PY)
    set fn_py2tcl $env(NOTCL_PIPE_PY2TCL)

    if $env(NOTCL_DEBUG_TCL) {
        proc log {message} {
            puts "\[notcl\] Tcl: $message"
        }
    } else {
        proc log {message} {}
    }

    variable base64_impl
    variable fn_py2tcl
    variable fn_tcl2py

    if {[catch {package require base64}]} {
        # Error thrown - package not found.
        log "Using built-in base64 implementation."
        set base64_impl builtin
    } else {
        log "Using base64 package."
        set base64_impl package
    }

    proc safe_obj_to_str {obj} {
        # This call to "format" copies the string value of data_in to data_in-str.
        # It prevents loss of opaque reference data due to conversion of
        # internal representation triggered by "binary encode" command.
        # To makes sure that this is not optimized away, we temporarily append
        # and then remove an 'X' character from the string.
        # (See also: "shimmering")

        set str [format "%sX" $obj]
        set str [string range $str 0 [expr [string length $str] - 2]]
        return $str
    }

    proc b64encode {data_in} {
        variable base64_impl

        set data_in [safe_obj_to_str $data_in]
        
        # -maxlen 0 prevents line wrapping by base64::encode, which would mess everything up.
        switch $base64_impl {
            package {
                return [base64::encode -maxlen 0 $data_in]
            }
            builtin {
                return [binary encode base64 -maxlen 0 $data_in]
            }
            default {
                return -code error "no base64 implementation selected"
            }
        }
    }

    proc b64decode {data_in} {
        variable base64_impl
        switch $base64_impl {
            package {
                return [base64::decode $data_in]
            }
            builtin {
                return [binary decode base64 $data_in]
            }
            default {
                return -code error "no base64 implementation selected"
            }
        }
    }

    proc sendmsg {msg} {
        variable fn_tcl2py
        
        log "sendmsg: opening tcl2py pipe $fn_tcl2py to send message..."
        set pipe [open $fn_tcl2py w]
        set first 1
        dict for {key value} $msg {
            if { ! $first } {
                puts $pipe {}
            }
            puts $pipe $key
            puts -nonewline $pipe [NoTcl::b64encode $value]
            set first 0
        }
        flush $pipe
        close $pipe
        log "sendmsg: message sent, tcl2py pipe $fn_tcl2py closed."
    }

    proc recvmsg {} {
        variable fn_py2tcl
        
        log "recvmsg: opening py2tcl pipe $fn_py2tcl to receive message..."
        set pipe [open $fn_py2tcl r]
        set msg {}
        while { ! [eof $pipe]} {
            set key [gets $pipe]
            set value [NoTcl::b64decode [gets $pipe]]
            dict append msg $key $value
        }
        close $pipe
        log "recvmsg: message received, py2tcl pipe $fn_py2tcl closed."
        return $msg
    }

    proc send_hello {} {
        set s_msg {}
        dict append s_msg "class" "TclHello"
        dict append s_msg "patchlevel" [info patchlevel]
        dict append s_msg "commands" [info commands]
        dict append s_msg "globals" [info globals]
        dict append s_msg "nameofexecutable" [info nameofexecutable]
        sendmsg $s_msg
    }

    proc send_proc_result {err_code cmd_idx result} {
        set s_msg {}
        dict append s_msg "class" "TclProcedureResult"
        dict append s_msg "err_code" $err_code
        dict append s_msg "cmd_idx" $cmd_idx
        dict append s_msg "result" $result
        sendmsg $s_msg
    }

    # The results are stored as $res($cmd_idx) array values in order to ensure that
    # Synopsys' collection handles are no automatically deleted / garbage collected.
    # Collection handles become invalid when no Tcl variables contain the reference
    # ("_selX") anymore. Obviously, this does not work with Python variables.
    variable cmd_idx
    variable cmd_results ;# This is an array
    
    set cmd_idx 0

    proc command_present {cmd} {
        return [expr [lsearch [info commands $cmd] $cmd] >= 0]
    }

    proc comm_loop {} {
        variable cmd_idx
        variable cmd_results

        set repr_supported [command_present "::tcl::unsupported::representation"]

        set pyexit_received 0
        while { ! $pyexit_received } {
            set r_msg [NoTcl::recvmsg]
            set class [dict get $r_msg class]
            switch $class {
                PyProcedureCall {
                    set cmd [dict get $r_msg command]

                    log "Executing command: $cmd"

                    set err_code [catch $cmd cmd_results($cmd_idx)]

                    # This should output something like: "Command finished, return value is a pure string with a refcount[...]"
                    # Unfortunately, this is not always supported.
                    #log "Command finished, return [::tcl::unsupported::representation $cmd_results($cmd_idx)]" 
                    if { $repr_supported } {
                        log "Command finished, returned [::tcl::unsupported::representation $cmd_results($cmd_idx)]."
                    } else {
                        log [format "Command finished, returned \"%s\"." $cmd_results($cmd_idx)]
                    }

                    send_proc_result $err_code $cmd_idx $cmd_results($cmd_idx)
                    set cmd_idx [expr $cmd_idx + 1]
                }
                PyExit {
                    set pyexit_received 1
                    set pyexit_quit [dict get $r_msg quit]
                }
                default {
                    puts "ERROR: Unknown message received"
                    set pyexit_received 1
                }
            }
        }
        return $pyexit_quit
    }

    proc main {} {
        NoTcl::send_hello
        if { [ NoTcl::comm_loop ] } {
            exit
        }
    }
}

NoTcl::main
