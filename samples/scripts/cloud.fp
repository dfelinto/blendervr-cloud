varying float depth;
varying vec3 color;

void main()
{
    gl_FragColor.rgb = color;
    gl_FragColor.a = 0.2;

    if (depth < 0.00001)
        discard;
}
