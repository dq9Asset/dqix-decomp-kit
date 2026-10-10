#include <globaldefs.h>

struct ItemInfoWindow_021ddc98 {
    char pad0[0x77c];
    signed char screen_;
};

struct Statics_021ddc98 {
    void* sDrops;
    void* sBuffer;
    void* sFieldNames;
    int sPalette;
    int sPalette2;
    void* sTexts;
    int sPalette3;
    int sStatesGuard;
    ItemInfoWindow_021ddc98* sWindow;
};
extern "C" Statics_021ddc98 data_ov023_021ff9e0;

struct Canvas_021ddc98 {
    char pad0[0xa8];
    short width_;
    short height_;
    short x_;
    short y_;
};

void CleanInvalidateCacheRange(const void* addr, unsigned int size);
extern "C" void LoadToSubBG0CharacterData(const void* src, unsigned int offset, unsigned int size);
extern "C" void LoadToMainBG1CharacterData(const void* src, unsigned int offset, unsigned int size);
extern "C" void LoadToMainBG2CharacterData(const void* src, unsigned int offset, unsigned int size);
extern "C" unsigned short* func_ov023_021db2b8(signed char screen, int bg1);

// USA: func_ov023_021ddc98
extern "C" ARM unsigned int func_ov023_021ddc98(Canvas_021ddc98* canvas, unsigned int offset, unsigned short palette, int bg1)
{
    unsigned int size = 0;
    short width;
    signed char screen;
    short height;
    int x;
    unsigned int tile;
    int y;
    unsigned short* base;
    short i;
    unsigned short* tiles;
    short j;
    unsigned short value;
    if (data_ov023_021ff9e0.sBuffer != NULL && canvas != NULL)
    {
        width = canvas->width_;
        screen = data_ov023_021ff9e0.sWindow->screen_;
        height = canvas->height_;
        size = (width * height) << 5;
        x = canvas->x_;
        y = canvas->y_;
        if (screen == 1)
        {
            CleanInvalidateCacheRange(data_ov023_021ff9e0.sBuffer, size);
            LoadToSubBG0CharacterData(data_ov023_021ff9e0.sBuffer, offset, size);
        }
        else
        {
            CleanInvalidateCacheRange(data_ov023_021ff9e0.sBuffer, size);
            if (bg1)
                LoadToMainBG1CharacterData(data_ov023_021ff9e0.sBuffer, offset, size);
            else
                LoadToMainBG2CharacterData(data_ov023_021ff9e0.sBuffer, offset, size);
        }
        tile = (offset << 11) >> 16;
        base = func_ov023_021db2b8(screen, bg1);
        if (base != NULL)
        {
            for (i = 0; i < height; i++)
            {
                tiles = base + (y << 5) + x;
                for (j = 0; j < width; j++)
                {
                    value = tile;
                    value |= palette << 12;
                    CleanInvalidateCacheRange(&value, 2);
                    *tiles = value;
                    tile = (unsigned short)(tile + 1);
                    tiles++;
                }
                y++;
            }
        }
    }
    return size;
}
