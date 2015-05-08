uniform sampler2D color_map;

const float width = 640.0;  /* number of horizontal vertices */
const float height = 480.0; /* number of vertical vertices */

void main()
{
    vec2 uv = gl_TexCoord[0].st;
    vec4 color = texture2D(color_map, uv);

    /* color */
    gl_FragColor = color;
    gl_FragColor.a = 1.0;

    /* barycentric uv to draw only points */
    vec2 cell_size;
    cell_size.x = 1.0 / (width - 1.0);
    cell_size.y = 1.0 / (height - 1.0);

    vec2 b_uv;
    b_uv.x = mod(uv.x, cell_size.x);
    b_uv.y = mod(uv.y, cell_size.y);

    vec2 point_size = cell_size * 0.9;

    if (((b_uv.x > point_size.x) &&
         (b_uv.x < 1.0 - point_size.x)) ||
        ((b_uv.y > point_size.y) &&
         (b_uv.y < 1.0 - point_size.y)))
    {
        discard;
    }

    /* culling to discard the background */
    if (color.a > 0.999) {
        discard;
    }
    else {
        gl_FragColor.a = 1.0;
    }
}
