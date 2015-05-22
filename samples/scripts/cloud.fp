uniform sampler2D color_map;
uniform sampler2D depth_map;

const float width = 640.0;  /* number of horizontal vertices */
const float height = 480.0; /* number of vertical vertices */

const float point_size = 0.9;

void main()
{
    vec2 uv = gl_TexCoord[0].st;
    vec4 color = texture2D(color_map, uv);
    float depth = texture2D(depth_map, uv).r;

    /* color */
    gl_FragColor = color;
    gl_FragColor.a = 1.0;

#if 0
    /* barycentric uv to draw only points */
    vec2 cell_size;
    cell_size.x = 1.0 / (width - 1.0);
    cell_size.y = 1.0 / (height - 1.0);

    vec2 b_uv;
    b_uv.x = mod(uv.x, cell_size.x) / cell_size.x;
    b_uv.y = mod(uv.y, cell_size.y) / cell_size.y;


    b_uv.x = mod((b_uv.x + 0.5), 1.0) * 2.0 - 1.0;
    b_uv.y = mod((b_uv.y + 0.5), 1.0) * 2.0 - 1.0;

    float radius = sqrt(b_uv.x * b_uv.x + b_uv.y * b_uv.y);

    if (radius > point_size) {
        discard;
    }

    /* culling to discard the background */
    if (depth > 0.999) {
        discard;
    }
#endif
}
