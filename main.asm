section .data
    num1 dd 5          ; Первое число (dd = define double word, 4 байта)
    num2 dd 3          ; Второе число
    result dd 0        ; Переменная для результата
    msg db "Результат: ", 0 ; Строка для вывода
    newline db 10      ; Символ новой строки (ASCII 10 = '\n')

section .bss
    buffer resb 12     ; Буфер для преобразования числа в строку

section .text
    global _start

_start:
    ; 1. Сложение чисел
    mov eax, [num1]    ; Загружаем первое число в регистр EAX
    add eax, [num2]    ; Прибавляем второе число к EAX
    mov [result], eax  ; Сохраняем результат в память

    ; 2. Подготовка к выводу строки "Результат: "
    mov eax, 4         ; Номер системного вызова sys_write
    mov ebx, 1         ; Файловый дескриптор stdout
    mov ecx, msg       ; Указатель на строку
    mov edx, 11        ; Длина строки (11 символов)
    int 0x80           ; Вызов ядра

    ; 3. Преобразование числа в строку (функция itoa)
    mov eax, [result]  ; Загружаем результат в EAX
    mov edi, buffer    ; Указываем на конец буфера
    add edi, 11        ; (буфер 12 байт, последний индекс 11)
    mov byte [edi], 0  ; Записываем нулевой терминатор строки
    mov ebx, 10        ; Основание системы счисления (десятичная)

.convert_loop:
    dec edi            ; Двигаемся назад по буферу
    xor edx, edx       ; Обнуляем EDX для деления
    div ebx            ; Делим EAX на 10, результат в EAX, остаток в EDX
    add dl, '0'        ; Преобразуем цифру в символ (ASCII)
    mov [edi], dl      ; Сохраняем символ в буфер
    test eax, eax      ; Проверяем, не ноль ли результат деления
    jnz .convert_loop  ; Если не ноль, продолжаем

    ; 4. Вывод числа
    mov ecx, edi       ; ECX = начало строки с числом
    mov edx, buffer    ; EDX = начало буфера
    add edx, 12        ; EDX = конец буфера
    sub edx, ecx       ; Вычисляем длину строки (конец - начало)
    mov eax, 4         ; sys_write
    mov ebx, 1         ; stdout
    int 0x80           ; Вызов ядра

    ; 5. Вывод новой строки
    mov eax, 4
    mov ebx, 1
    mov ecx, newline
    mov edx, 1
    int 0x80

    ; 6. Завершение программы
    mov eax, 1         ; sys_exit
    mov ebx, 0         ; код возврата 0
    int 0x80