#version 120
varying vec3 fragPos;
varying vec3 fragNormal;

void main() {
    vec3 toLight  = -fragPos;
    float dist    = length(toLight);
    vec3 lightDir = toLight / dist;

    vec3  spotDir = vec3(0.0, 0.0, -1.0);
    float angle   = degrees(acos(clamp(dot(-lightDir, spotDir), -1.0, 1.0)));

    float ambient = 0.05;

    // smoothstep fades from 1.0 at 0° to 0.0 between innerCutoff and outerCutoff
    float innerCutoff = 35.0;  // full brightness inside this angle
    float outerCutoff = 55.0;  // fully faded by this angle

    float spot   = pow(max(dot(-lightDir, spotDir), 0.0), 6.0);
    float diff   = max(dot(fragNormal, lightDir), 0.0);
    float atten  = 1.0 / (0.5 + 0.2 * dist + 0.05 * dist * dist);

    // 1.0 inside cone, smooth gradient between inner and outer, 0.0 outside
    float cone   = 1.0 - smoothstep(innerCutoff, outerCutoff, angle);

    float light  = ambient + diff * spot * atten * cone;
    gl_FragColor = vec4(gl_Color.rgb * light, 1.0);
}