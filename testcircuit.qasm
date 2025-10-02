OPENQASM 3.0;
include "stdgates.inc";
gate sxdg _gate_q_0 {
  s _gate_q_0;
  h _gate_q_0;
  s _gate_q_0;
}
gate xx_minus_yy(p0, p1) _gate_q_0, _gate_q_1 {
  rz(-p1) _gate_q_1;
  sdg _gate_q_0;
  sx _gate_q_0;
  s _gate_q_0;
  s _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  ry(0.5*p0) _gate_q_0;
  ry((-0.5)*p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  sdg _gate_q_1;
  sdg _gate_q_0;
  sxdg _gate_q_0;
  s _gate_q_0;
  rz(p1) _gate_q_1;
}
gate cu1(p0) _gate_q_0, _gate_q_1 {
  p(0.5*p0) _gate_q_0;
  cx _gate_q_0, _gate_q_1;
  p((-0.5)*p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  p(0.5*p0) _gate_q_1;
}
gate rxx(p0) _gate_q_0, _gate_q_1 {
  h _gate_q_0;
  h _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  rz(p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  h _gate_q_1;
  h _gate_q_0;
}
qubit[5] q;
xx_minus_yy(4.938987693414485, 0.8049616944763924) q[0], q[3];
cu1(2.829858307545725) q[4], q[2];
rz(2.3297926977893746) q[1];
ry(4.763205750057398) q[4];
ch q[2], q[0];
x q[1];
ry(2.2275523539672073) q[3];
rxx(4.291723147097387) q[4], q[2];
rx(4.679478635343389) q[0];
y q[3];
sx q[1];
U(1.4257134880181992, 4.208565449932414, 2.746706513663991) q[2];
y q[3];
rx(5.2318714070794075) q[4];
h q[0];
y q[1];
