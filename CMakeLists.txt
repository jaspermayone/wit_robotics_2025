cmake_minimum_required(VERSION 3.13)

set(PICO_BOARD pico2_w CACHE STRING "Board type")
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(BLUEPAD32_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/bluepad32)

# Use BTstack from Pico SDK
set(BTSTACK_ROOT ${PICO_SDK_PATH}/lib/btstack)

# initialize the SDK based on PICO_SDK_PATH
# note: this must happen before project()
include(pico_sdk_import.cmake)

project(monster_book C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# initialize the Raspberry Pi Pico SDK
pico_sdk_init()

add_executable(${PROJECT_NAME}
    src/main.c
    src/bluetooth/my_platform.c
    src/hardware/motor.c
    src/hardware/motor_controller.c
    src/hardware/telemetry.c
    src/networking/wifi_ap.c
    src/networking/web_server.c
    src/networking/dhcpserver/dhcpserver.c
)

target_include_directories(${PROJECT_NAME} PRIVATE
    src
    src/config
    src/hardware
    src/networking
    src/networking/dhcpserver
    src/bluetooth
    ${BLUEPAD32_ROOT}/src/components/bluepad32/include
)

# Needed for btstack_config.h / sdkconfig.h
include_directories(${PROJECT_NAME} src/config)

# Needed for BTstack includes
include_directories(${BTSTACK_ROOT}/3rd-party/bluedroid/encoder/include)
include_directories(${BTSTACK_ROOT}/3rd-party/bluedroid/decoder/include)
include_directories(${BTSTACK_ROOT}/src)

target_link_libraries(${PROJECT_NAME} PUBLIC
    pico_stdlib
    pico_cyw43_arch_lwip_threadsafe_background
    pico_btstack_classic
    pico_btstack_cyw43
    hardware_pwm
    hardware_adc
    bluepad32
)

add_subdirectory(${BLUEPAD32_ROOT}/src/components/bluepad32 libbluepad32)

# Enable USB serial output
pico_enable_stdio_usb(${PROJECT_NAME} 1)
pico_enable_stdio_uart(${PROJECT_NAME} 0)

# create map/bin/hex/uf2 file in addition to ELF.
pico_add_extra_outputs(${PROJECT_NAME})
