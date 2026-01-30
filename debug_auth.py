import streamlit_authenticator as stauth
import inspect

print("\nHasher Init:", inspect.signature(stauth.Hasher.__init__))
print("\nAuthenticate Init:", inspect.signature(stauth.Authenticate.__init__))
