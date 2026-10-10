// Synthetic source exercising each new colorsweep rule exactly once. Not compiled -- rulecheck.py
// reads it to prove a rule fires on the shape it was written for, and on nothing else.
#include <globaldefs.h>

extern "C" void Sink(int a, int b);
extern "C" int Get(void *p);

extern "C" ARM int Probe(void *ctx, int *out, int k) {
    if (*((unsigned char *)ctx + 0x100d) <= 1)
        return 0;
    *out = (k == 3) ? 7 : 9;
    Sink(k == 0, 1);
    Sink((short)k, 2);
    int last = k - 1;
    Sink(last, 3);
    return 1;
}
