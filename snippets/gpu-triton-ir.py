Triton-IR, an LLVM-based intermediate representation in which multi-dimensional blocks of values are first-class citizens.

- Python
@jit
def add(X, Y, Z, N):
   pid = program_id(0)
   idx= pid * 512 + arange(512)
   mask = idx < N
   x = load(X + idx, mask=mask)
   y = load(Y + idx, mask=mask)
   store(Z + idx, x + y, mask=mask)

-> AST visitor
- Triton IR

def void add(i32* X .aligned(16) , i32* Y .aligned(16) , i32* Z .aligned(16) , i32 N .multipleof(2) )
{
entry:
  %0 = get_program_id[0] i32;
  %1 = mul i32 %0, 512;
  %3 = make_range[0 : 512] i32<512>;
  %4 = splat i32<512> %1;
  %6 = add i32<512> %4, %3;
  %9 = splat i32<512> N;
  %11 = icmp_slt i1<512> %6, %9;
  %14 = splat i32*<512> X;
  %16 = getelementptr i32*<512> %14, %6;
  %19 = broadcast i1<512> %11;
  %21 = splat i32<512> undef;
  %22 = masked_load i32<512> %16, %19, %21;
  %26 = splat i32*<512> Y;
  %28 = getelementptr i32*<512> %26, %6;
  %31 = broadcast i1<512> %11;
  %33 = splat i32<512> undef;
  %34 = masked_load i32<512> %28, %31, %33;
  %38 = splat i32*<512> Z;
  %40 = getelementptr i32*<512> %38, %6;
  %43 = add i32<512> %22, %34;
  %46 = broadcast i32<512> %43;
  %48 = broadcast i1<512> %11;
  masked_store void %40, %46, %48;
  ret void;
}

-> Triton Compiler
- LLVM IR

-> libLLVM
- PTX

.visible .entry add(
    .param .u64 add_param_0, .param .u64 add_param_1,
    .param .u64 add_param_2, .param .u32 add_param_3
)
.maxntid 128, 1, 1
{
    .reg .pred     %p<4>;
    .reg .b32     %r<18>;
    .reg .b64     %rd<8>;
    ld.param.u64     %rd4, [add_param_0];
    ld.param.u64     %rd5, [add_param_1];
    mov.u32     %r13, %tid.x;
    ld.param.u32     %r14, [add_param_3];
    shl.b32     %r15, %r13, 2;
    mov.u32     %r16, %ctaid.x;
    mad.lo.s32     %r17, %r16, 512, %r15;
    setp.ge.s32     %p3, %r17, %r14;
    setp.lt.s32     %p1, %r17, %r14;
    mul.wide.s32     %rd7, %r17, 4;
    add.s64     %rd2, %rd4, %rd7;
    @%p1 ld.global.cg.v4.b32 {%r5,%r6,%r7,%r8}, [ %rd2 + 0];
    add.s64     %rd3, %rd5, %rd7;
    @%p1 ld.global.cg.v4.b32 {%r9,%r10,%r11,%r12}, [ %rd3 + 0];
    @%p3 bra     LBB0_2;
    ld.param.u64     %rd6, [add_param_2];
    add.s64     %rd1, %rd6, %rd7;
    add.s32     %r1, %r5, %r9;
    add.s32     %r2, %r6, %r10;
    add.s32     %r3, %r7, %r11;
    add.s32     %r4, %r8, %r12;
    st.global.v4.u32     [%rd1], {%r1, %r2, %r3, %r4};
LBB0_2:
    ret;
}