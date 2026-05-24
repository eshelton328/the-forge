# HRO_TypeC_USB (fork)

Copy of KiCad **`Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12`** with mechanical shield pads renamed from **`SH` → `S1`**.

KiCad **`Connector:USB_C_Receptacle_USB2.0_14P`** uses shield pin **`S1`**. The stock KiCad footprint uses **`SH`** for those pads, so **Update PCB from schematic** fails until the pad names align.

Pads **`A8` / `B8`** (SBUs) remain; the 14P symbol has no nets for them—KiCad may still warn unless you migrate to **`USB_C_Receptacle_USB2.0_16P`** and mark SBUs **NC** / **no-connect** as appropriate.
