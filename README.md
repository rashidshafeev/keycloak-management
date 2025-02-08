1. Download the script:
```bash
curl -O https://raw.githubusercontent.com/yourusername/keycloak-management/main/install.sh
chmod +x install.sh
```

2. Run it:
```bash
sudo ./install.sh
```

3. Use the deployment tool:
```bash
sudo keycloak-deploy --domain example.com --email admin@example.com
```

Place this script as `install.sh` in your repository root. Add these lines to your README.md to explain the one-line installation:

```bash
curl -sSL https://raw.githubusercontent.com/yourusername/keycloak-management/main/install.sh | sudo bash
```

The script handles:
1. Repository cloning
2. Environment setup
3. Dependency installation
4. Creates a global command for easier access
5. Proper logging of the installation process

Would you like me to help with setting up the repository structure or adding any additional automation features?