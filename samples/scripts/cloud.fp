varying float depth_normal;
varying vec3 color;

void main()
{
    gl_FragColor.rgb = color;
    gl_FragColor.a = 0.2;

    /* black is the NULL data */
    if (depth_normal < 0.00001)
        discard;
}
