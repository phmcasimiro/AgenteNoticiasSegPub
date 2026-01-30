import streamlit_authenticator as stauth
import sys

def generate():
    print("🔐 Gerador de Hashes de Senha (Streamlit Authenticator)")
    print("-" * 50)
    
    passwords = []
    if len(sys.argv) > 1:
        passwords = sys.argv[1:]
    else:
        print("Digite as senhas para gerar hash (pressione Enter vazio para finalizar):")
        while True:
            pwd = input("Senha: ")
            if not pwd:
                break
            passwords.append(pwd)

    if not passwords:
        print("Nenhuma senha fornecida.")
        return

    print("\nGerando hashes...")
    try:
        hashed_passwords = stauth.Hasher.hash_list(passwords)
        
        print("\n✅ Hashes Geradas com Sucesso:")
        for plain, hashed in zip(passwords, hashed_passwords):
            print(f"\nSenha: {plain}")
            print(f"Hash:  {hashed}")
            
        print("\n➡️  Copie a linha 'Hash' para o seu arquivo auth_config.yaml na seção 'password'.")
            
    except Exception as e:
        print(f"❌ Erro ao gerar hashes: {e}")

if __name__ == "__main__":
    generate()
