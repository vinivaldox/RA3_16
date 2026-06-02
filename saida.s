.data
    .align 3
    memoria_res: .space 800
    const_um: .double 1.0
    num_0: .double 1
    var_I: .double 0.0

.text
.global _start
_start:
    @ START
    LDR r0, =num_0
    VLDR.F64 d0, [r0]
    VPUSH {d0}
    LDR r0, =var_I
    VLDR.F64 d0, [r0]
    VPUSH {d0}
    @ MEM: armazena valor na variável
    VPOP {d1}
    VPOP {d0}
    LDR r0, =var_I
    VSTR.F64 d0, [r0]
    @ END
    BX lr
