#!/bin/bash

# Parametry rsync
RSYNC_OPTIONS="-avxHAX"

# Ścieżka źródłowa (z ukośnikiem na końcu)
SOURCE_DIR="/mnt/"

# Ścieżka docelowa
DEST_DIR="/mnt"

# Zakres hostów
for i in {1..16}; do
    # Pomijamy hosty 3 i 4
    if [[ "$i" -eq 3 || "$i" -eq 4 ]]; then
        continue
    fi

    # Nazwa hosta
    HOST="student@lab-sec-$i"

    # Uruchamianie rsync
    rsync $RSYNC_OPTIONS "$SOURCE_DIR" "$HOST:$DEST_DIR"

    # Sprawdzenie statusu wykonania
    if [[ $? -eq 0 ]]; then
        echo "Przesłano do $HOST pomyślnie."
    else
        echo "Błąd przesyłania do $HOST."
    fi
done
