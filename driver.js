print("DRIVER:READY");
while (true) {
    var file = readline();
    if (!file)
	break;
    load(file);
    timeout(-1);
    print("DRIVER:OK");
}
