#include <globaldefs.h>

class GameState
{
public:
    static GameState* GetInstance();
};

struct Canvas_021db634;

struct LayoutElement_021db634 {
    char pad0[0x16];
    unsigned char flags_;
    unsigned char unk_17;
};

struct Layout_021db634 {
    int unk_0;
    Canvas_021db634* canvas_;
    char pad8[0x12 - 8];
    short unk_12;
};

struct ItemInfoEntry_021db634
{
    unsigned char unk_0;
    unsigned char enabled_;
    short unk_2;
    const char* text_;
};

struct ItemInfoList_021db634
{
    short unk_0;
    short count_;
    ItemInfoEntry_021db634* entries_;
};

struct ItemInfoTable_021db634
{
    char unk_0[8];
    ItemInfoList_021db634* list_;
    char unk_c[4];
};

struct IntBytePair021dbb20
{
    const char* text_;
    unsigned char kind_;
};

struct Container020e0310;
struct Obj_0201bb78;
struct StructAcAe021db45c;

struct Statics_021db634 {
    void* sDrops;
    void* sBuffer;
    struct Container020e0310* sFieldNames;
    int sPalette;
    int sPalette2;
    struct Container020e0310* sTexts;
    int sPalette3;
    int sStatesGuard;
    void* sWindow;
    ItemInfoTable_021db634* sPlaces;
};
extern "C" Statics_021db634 data_ov023_021ff9e0;
extern "C" const short data_ov023_021fd5b8[3];

const char* GetFieldByKey020e0434(struct Container020e0310* c, int key);
const char* CallFunc020e0434With02153694(int id);
extern "C" LayoutElement_021db634* func_ov023_021db4e4(Layout_021db634* layout, int id);
void SetEntryFields_021e23d0(void* layout, int id, int text, unsigned char color, unsigned char shadow);
extern "C" void* memset(void* dst, int value, unsigned int length);
extern "C" unsigned int strlen(const char* text);
extern "C" void __clear(void* buffer, unsigned long size);
extern "C" void* memcpy(void* dst, const void* src, unsigned int length);
extern "C" long func_02005a94(const char* text);
extern "C" void* func_02012fe4();
int LookupBitFromValueRange0201bb78(struct Obj_0201bb78* flags, unsigned int id);
extern "C" void* func_0205ec34();
int TestBitInByteArray(int flags, unsigned char* flags2, int id);
extern "C" void func_020ac2d4(int, short* ids, void* results, int count);
int BuildBitmask0206e384(unsigned char* flags);
int GetShortFromTable0206e3d4(int flags, int index);
unsigned int ParseCodeLetter_021db564(char* text);
void CopyIntAndByte_021dbb20(struct IntBytePair021dbb20* dst, struct IntBytePair021dbb20* src);
int GetField5cb0Value(char* gameState);
void UpdateEntryAndReset_021db45c(void* layout, struct StructAcAe021db45c* canvas, int id, short* x, short* y);
extern "C" void func_ov023_021e257c(Layout_021db634* layout);
void CreateAndSetFields8A_021db544(void* layout, void* id, int x, int y);

#define SHOW_ELEMENT(layout, id)                                           \
    {                                                                      \
        LayoutElement_021db634* element = func_ov023_021db4e4(layout, id); \
        if (element != NULL)                                               \
            element->flags_ |= 1;                                          \
    }

#define HIDE_ELEMENT(layout, id)                                           \
    {                                                                      \
        LayoutElement_021db634* element = func_ov023_021db4e4(layout, id); \
        if (element != NULL)                                               \
            element->flags_ &= ~1;                                         \
    }

// USA: func_ov023_021db634
extern "C" ARM void func_ov023_021db634(Layout_021db634* layout, Canvas_021db634* canvas)
{
    const char* found;
    const char* none;
    const char* trade;
    const char* alchemy;
    IntBytePair021dbb20 places[4];
    ItemInfoList_021db634* list;
    ItemInfoEntry_021db634* entry;
    short entries;
    unsigned char shown;
    int last;
    int i2;
    int j;
    int i3;
    unsigned char count;
    int i;
    found = GetFieldByKey020e0434(data_ov023_021ff9e0.sTexts, 0x1f);
    none = GetFieldByKey020e0434(data_ov023_021ff9e0.sTexts, 0x1e);
    trade = GetFieldByKey020e0434(data_ov023_021ff9e0.sTexts, 0x2a);
    alchemy = CallFunc020e0434With02153694(0x56);
    SHOW_ELEMENT(layout, 0xf);
    SHOW_ELEMENT(layout, 0xa);
    SetEntryFields_021e23d0(layout, 7, (int)found, 10, 15);
    SetEntryFields_021e23d0(layout, 8, (int)found, 10, 15);
    SetEntryFields_021e23d0(layout, 9, (int)found, 10, 15);
    SetEntryFields_021e23d0(layout, 0xa, (int)none, 10, 15);
    memset(places, 0, sizeof(places));
    count = 0;
    list = data_ov023_021ff9e0.sPlaces->list_;
    if (list != NULL)
    {
        i = 0;
        entry = list->entries_;
        entries = list->count_;
        for (; i < entries; i++, entry++)
        {
            IntBytePair021dbb20 place;
            place.text_ = NULL;
            place.kind_ = 0;
            if (!entry->enabled_)
                continue;
            const char* text = entry->text_;
            if (text != NULL)
            {
            char c = text[0];
            if (c == 'f')
            {
                if (strlen(text) >= 5)
                {
                    char number[4] = {0};
                    memcpy(number, entry->text_ + 2, 2);
                    short field = func_02005a94(number);
                    if (!LookupBitFromValueRange0201bb78((Obj_0201bb78*)func_02012fe4(), (unsigned short)(field + 20000)))
                        continue;
                    text = GetFieldByKey020e0434(data_ov023_021ff9e0.sFieldNames, (short)func_02005a94(entry->text_ + 5));
                    place.kind_ = 2;
                }
            }
            else if (c == 'a')
            {
                short recipe = func_02005a94(text + 1);
                void* flags = func_0205ec34();
                if (!TestBitInByteArray((int)flags, (unsigned char*)flags + 0x8c, 0x1198))
                    continue;
                struct
                {
                    short id_;
                    unsigned short known_ : 1;
                } result;
                memset(&result, 0, sizeof(result));
                func_020ac2d4(0, &recipe, &result, 1);
                if (result.id_ == 0 || !result.known_)
                    continue;
                place.kind_ = 1;
                text = alchemy;
            }
            else if (c == 'b')
            {
                void* flags = func_0205ec34();
                int bits = BuildBitmask0206e384((unsigned char*)flags);
                if (!((1 << (GetShortFromTable0206e3d4((int)flags, 0x17) - 1)) & (bits << 0x10)))
                    continue;
                place.kind_ = 3;
                text = trade;
            }
            else if (c >= 'A' && c <= 'Z')
            {
                void* flags = func_02012fe4();
                unsigned short id = ParseCodeLetter_021db564((char*)entry->text_);
                if (id == 0)
                    continue;
                if (!LookupBitFromValueRange0201bb78((Obj_0201bb78*)flags, id))
                    continue;
                text = GetFieldByKey020e0434(data_ov023_021ff9e0.sFieldNames, (short)id);
                place.kind_ = 4;
            }
            }
            if (text == NULL)
                continue;
            place.text_ = text;
            CopyIntAndByte_021dbb20(&places[count], &place);
            count++;
            if (count == 4)
                break;
        }
    }
    if (GetField5cb0Value((char*)GameState::GetInstance()) == 1)
        count = 0;
    shown = count;
    if (count == 4)
        shown = 3;
    last = shown - 1;
    for (i2 = 0; i2 < last; i2++)
    {
        for (j = 0; j < last - i2; j++)
        {
            if (places[j].kind_ < places[j + 1].kind_)
            {
                IntBytePair021dbb20 place = places[j];
                CopyIntAndByte_021dbb20(&places[j], &places[j + 1]);
                CopyIntAndByte_021dbb20(&places[j + 1], &place);
            }
        }
    }
    for (i3 = 0; i3 < 3; i3++)
    {
        if (i3 == count)
            break;
        SetEntryFields_021e23d0(layout, data_ov023_021fd5b8[i3], (int)places[i3].text_, 10, 15);
    }
    if (count != 4)
        HIDE_ELEMENT(layout, 0xa);
    short x;
    short y;
    UpdateEntryAndReset_021db45c(layout, (StructAcAe021db45c*)canvas, 0xf, &x, &y);
    if (data_ov023_021ff9e0.sBuffer != NULL)
    {
        layout->canvas_ = canvas;
        layout->unk_12 = 1;
        func_ov023_021e257c(layout);
    }
    CreateAndSetFields8A_021db544(layout, (void*)0xf, x, y);
    HIDE_ELEMENT(layout, 0xf);
}
