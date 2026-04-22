//#include "fmc.h"
//
//#define SDRAM_MODEREG_BURST_LENGTH_1        0x0000
//#define SDRAM_MODEREG_BURST_TYPE_SEQUENTIAL 0x0000
//#define SDRAM_MODEREG_CAS_LATENCY_2         0x0020
//#define SDRAM_MODEREG_WRITEBURST_MODE_SINGLE 0x0200
//
//void SDRAM_Init(void)
//{
//    FMC_SDRAM_CommandTypeDef cmd = {0};
//    uint32_t tmpr = 0;
//
//    /* 1. Clock enable */
//    cmd.CommandMode           = FMC_SDRAM_CMD_CLK_ENABLE;
//    cmd.CommandTarget         = FMC_SDRAM_CMD_TARGET_BANK1;
//    cmd.AutoRefreshNumber     = 1;
//    cmd.ModeRegisterDefinition = 0;
//    HAL_SDRAM_SendCommand(&hsdram1, &cmd, 0xFFFF);
//    HAL_Delay(1);
//
//    /* 2. Precharge all */
//    cmd.CommandMode = FMC_SDRAM_CMD_PALL;
//    HAL_SDRAM_SendCommand(&hsdram1, &cmd, 0xFFFF);
//
//    /* 3. Auto-refresh (×8) */
//    cmd.CommandMode       = FMC_SDRAM_CMD_AUTOREFRESH_MODE;
//    cmd.AutoRefreshNumber = 8;
//    HAL_SDRAM_SendCommand(&hsdram1, &cmd, 0xFFFF);
//
//    /* 4. Load mode register */
//    tmpr = SDRAM_MODEREG_BURST_LENGTH_1        |
//           SDRAM_MODEREG_BURST_TYPE_SEQUENTIAL  |
//           SDRAM_MODEREG_CAS_LATENCY_2          |
//           SDRAM_MODEREG_WRITEBURST_MODE_SINGLE;
//
//    cmd.CommandMode            = FMC_SDRAM_CMD_LOAD_MODE;
//    cmd.AutoRefreshNumber      = 1;
//    cmd.ModeRegisterDefinition = tmpr;
//    HAL_SDRAM_SendCommand(&hsdram1, &cmd, 0xFFFF);
//
//    /* 5. Refresh rate: 120MHz / 64ms / 4096 vrstic - 20 = ~1754 */
//    HAL_SDRAM_ProgramRefreshRate(&hsdram1, 1754);
//}
