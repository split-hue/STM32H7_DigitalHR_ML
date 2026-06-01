################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (12.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Drivers/STM32H750B-DK/stm32h750b_discovery.c \
../Drivers/STM32H750B-DK/stm32h750b_discovery_bus.c \
../Drivers/STM32H750B-DK/stm32h750b_discovery_lcd.c \
../Drivers/STM32H750B-DK/stm32h750b_discovery_qspi.c \
../Drivers/STM32H750B-DK/stm32h750b_discovery_sdram.c \
../Drivers/STM32H750B-DK/stm32h750b_discovery_ts.c 

OBJS += \
./Drivers/STM32H750B-DK/stm32h750b_discovery.o \
./Drivers/STM32H750B-DK/stm32h750b_discovery_bus.o \
./Drivers/STM32H750B-DK/stm32h750b_discovery_lcd.o \
./Drivers/STM32H750B-DK/stm32h750b_discovery_qspi.o \
./Drivers/STM32H750B-DK/stm32h750b_discovery_sdram.o \
./Drivers/STM32H750B-DK/stm32h750b_discovery_ts.o 

C_DEPS += \
./Drivers/STM32H750B-DK/stm32h750b_discovery.d \
./Drivers/STM32H750B-DK/stm32h750b_discovery_bus.d \
./Drivers/STM32H750B-DK/stm32h750b_discovery_lcd.d \
./Drivers/STM32H750B-DK/stm32h750b_discovery_qspi.d \
./Drivers/STM32H750B-DK/stm32h750b_discovery_sdram.d \
./Drivers/STM32H750B-DK/stm32h750b_discovery_ts.d 


# Each subdirectory must supply rules for building sources it contributes
Drivers/STM32H750B-DK/%.o Drivers/STM32H750B-DK/%.su Drivers/STM32H750B-DK/%.cyclo: ../Drivers/STM32H750B-DK/%.c Drivers/STM32H750B-DK/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m7 -std=gnu11 -g3 -DDEBUG -DUSE_HAL_DRIVER -DSTM32H750xx -c -I../Core/Inc -I../Drivers/STM32H7xx_HAL_Driver/Inc -I../Drivers/STM32H7xx_HAL_Driver/Inc/Legacy -I../Drivers/CMSIS/Device/ST/STM32H7xx/Include -I../Drivers/CMSIS/Include -I../X-CUBE-AI/App -I../X-CUBE-AI -I../Middlewares/ST/AI/Inc -I../Middlewares/Third_Party/FreeRTOS/Source/include -I../Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2 -I../Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM4F -I../Drivers/BSP/Components -I../Core/Src -I../Drivers/BSP/Components/Common -I../Drivers/STM32H750B-DK -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv5-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Drivers-2f-STM32H750B-2d-DK

clean-Drivers-2f-STM32H750B-2d-DK:
	-$(RM) ./Drivers/STM32H750B-DK/stm32h750b_discovery.cyclo ./Drivers/STM32H750B-DK/stm32h750b_discovery.d ./Drivers/STM32H750B-DK/stm32h750b_discovery.o ./Drivers/STM32H750B-DK/stm32h750b_discovery.su ./Drivers/STM32H750B-DK/stm32h750b_discovery_bus.cyclo ./Drivers/STM32H750B-DK/stm32h750b_discovery_bus.d ./Drivers/STM32H750B-DK/stm32h750b_discovery_bus.o ./Drivers/STM32H750B-DK/stm32h750b_discovery_bus.su ./Drivers/STM32H750B-DK/stm32h750b_discovery_lcd.cyclo ./Drivers/STM32H750B-DK/stm32h750b_discovery_lcd.d ./Drivers/STM32H750B-DK/stm32h750b_discovery_lcd.o ./Drivers/STM32H750B-DK/stm32h750b_discovery_lcd.su ./Drivers/STM32H750B-DK/stm32h750b_discovery_qspi.cyclo ./Drivers/STM32H750B-DK/stm32h750b_discovery_qspi.d ./Drivers/STM32H750B-DK/stm32h750b_discovery_qspi.o ./Drivers/STM32H750B-DK/stm32h750b_discovery_qspi.su ./Drivers/STM32H750B-DK/stm32h750b_discovery_sdram.cyclo ./Drivers/STM32H750B-DK/stm32h750b_discovery_sdram.d ./Drivers/STM32H750B-DK/stm32h750b_discovery_sdram.o ./Drivers/STM32H750B-DK/stm32h750b_discovery_sdram.su ./Drivers/STM32H750B-DK/stm32h750b_discovery_ts.cyclo ./Drivers/STM32H750B-DK/stm32h750b_discovery_ts.d ./Drivers/STM32H750B-DK/stm32h750b_discovery_ts.o ./Drivers/STM32H750B-DK/stm32h750b_discovery_ts.su

.PHONY: clean-Drivers-2f-STM32H750B-2d-DK

