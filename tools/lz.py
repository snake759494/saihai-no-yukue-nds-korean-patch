def lz11(d):
    t=d[0]; n=int.from_bytes(d[1:4],'little'); p=4
    if n==0: n=int.from_bytes(d[4:8],'little'); p=8
    o=bytearray()
    while len(o)<n:
        f=d[p]; p+=1
        for b in range(8):
            if len(o)>=n: break
            if not f&(0x80>>b): o.append(d[p]); p+=1; continue
            if t==0x10:
                a=d[p];c=d[p+1];p+=2;L=(a>>4)+3;D=((a&15)<<8|c)+1
            else:
                a=d[p]; h=a>>4
                if h==0: L=((a&15)<<4|d[p+1]>>4)+0x11; D=((d[p+1]&15)<<8|d[p+2])+1; p+=3
                elif h==1: L=((a&15)<<12|d[p+1]<<4|d[p+2]>>4)+0x111; D=((d[p+2]&15)<<8|d[p+3])+1; p+=4
                else: L=h+1; D=((a&15)<<8|d[p+1])+1; p+=2
            for _ in range(L): o.append(o[-D])
    return bytes(o)
