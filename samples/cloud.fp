uniform sampler2D color_map;

void main()
{
    vec4 color = texture2D(color_map, gl_TexCoord[0].st);
    gl_FragColor = color;

    if (color.a > 0.999) {
        discard;
    }
    else {
        gl_FragColor.a = 1.0;
    }
}
