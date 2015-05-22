uniform sampler2D color_map;

varying vec2 vUv;

void main()
{
    vec4 color = texture2D(color_map, vUv);
    gl_FragColor = vec4(color.r, color.g, color.b, 0.2);

}
