#version 120
varying vec3 fragPos;
varying vec3 fragNormal;

void main() {
    fragPos     = vec3(gl_ModelViewMatrix * gl_Vertex);
    fragNormal  = normalize(gl_NormalMatrix * gl_Normal);
    gl_Position = gl_ProjectionMatrix * gl_ModelViewMatrix * gl_Vertex;
    gl_FrontColor = gl_Color;
}