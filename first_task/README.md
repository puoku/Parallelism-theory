**Сборка:**
```bash
cmake -S . -B build"
```
По умолчанию стоит тип double

**Чтобы использовать float, необходимо использовать флаг сборки:**
```bash
cmake -S . -B build -DUSE_FLOAT=ON
```

Сумма double: -5.25862e-11 <br>
Сумма float: 3.14626e-05