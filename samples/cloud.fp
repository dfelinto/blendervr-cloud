uniform sampler2D color_map;
varying vec4 coord_vec;

void main() {
    vec4 color = texture2D(color_map, gl_TexCoord[0].st);
    gl_FragColor = mix(color, coord_vec, 0.1);
}
