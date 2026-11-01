from convert import main as convert_json2toml
from build import main as build_toml2mrpack

def main(j2t = True, t2m = True):
    if j2t:
        return_j2t = convert_json2toml()
        print(return_j2t)
        if return_j2t[0] < 0:
            return False
    if t2m:
        return_t2m = build_toml2mrpack()
        print(return_t2m)
        if return_t2m[0] < 0:
            return False
    return True

if __name__ == "__main__":
    main(j2t=bool(int(input('j2t? '))),t2m=bool(int(input('t2m? '))))