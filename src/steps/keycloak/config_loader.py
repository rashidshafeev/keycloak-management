"""
Keycloak Configuration Loader

This module handles loading configuration templates and applying them to a Keycloak instance.
"""

import os
import yaml
import json
import logging
from pathlib import Path
from string import Template
from typing import Dict, Any, List, Optional

logger = logging.getLogger("step.keycloak_deployment.config_loader")

class ConfigLoader:
    """
    Loads and applies configuration templates to a Keycloak instance
    """
    
    def __init__(self, keycloak_container, admin_user: str, admin_password: str):
        """
        Initialize the configuration loader
        
        Args:
            keycloak_container: Docker container object for Keycloak
            admin_user: Keycloak admin username
            admin_password: Keycloak admin password
        """
        self.keycloak_container = keycloak_container
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.templates_dir = Path(__file__).parent / "config" / "templates"
        
    def load_template(self, template_name: str, variables: Dict[str, str]) -> Any:
        """
        Load a template file and substitute variables
        
        Args:
            template_name: Name of the template file (without extension)
            variables: Dictionary of variables to substitute
            
        Returns:
            Parsed YAML content with variables substituted
        """
        template_path = self.templates_dir / f"{template_name}.yml"
        
        if not template_path.exists():
            logger.error(f"Template {template_name}.yml not found")
            return None
            
        try:
            with open(template_path, 'r') as f:
                template_content = Template(f.read())
                
            # Substitute variables
            rendered_content = template_content.safe_substitute(variables)
            
            # Parse YAML
            return yaml.safe_load(rendered_content)
        except Exception as e:
            logger.error(f"Failed to load template {template_name}.yml: {e}")
            return None
    
    def authenticate_to_keycloak(self) -> bool:
        """
        Authenticate to Keycloak admin API
        
        Returns:
            bool: True if authentication was successful
        """
        try:
            logger.info("Authenticating to Keycloak")
            result = self.keycloak_container.exec_run([
                "/bin/bash", "-c", 
                f"/opt/keycloak/bin/kcadm.sh config credentials --server http://localhost:8080/auth --realm master --user {self.admin_user} --password {self.admin_password}"
            ])
            
            if result.exit_code != 0:
                logger.error(f"Authentication failed: {result.output.decode('utf-8')}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def create_realm(self, realm_config: Dict[str, Any]) -> bool:
        """
        Create or update a realm
        
        Args:
            realm_config: Realm configuration
            
        Returns:
            bool: True if successful
        """
        try:
            logger.info(f"Creating/updating realm: {realm_config.get('realm')}")
            
            # Convert to JSON
            realm_json = json.dumps(realm_config)
            
            # Check if realm exists
            check_result = self.keycloak_container.exec_run([
                "/bin/bash", "-c", 
                f"/opt/keycloak/bin/kcadm.sh get realms/{realm_config.get('realm')}"
            ])
            
            if check_result.exit_code == 0:
                # Update existing realm
                result = self.keycloak_container.exec_run([
                    "/bin/bash", "-c", 
                    f"echo '{realm_json}' | /opt/keycloak/bin/kcadm.sh update realms/{realm_config.get('realm')}"
                ])
            else:
                # Create new realm
                result = self.keycloak_container.exec_run([
                    "/bin/bash", "-c", 
                    f"echo '{realm_json}' | /opt/keycloak/bin/kcadm.sh create realms"
                ])
                
            if result.exit_code != 0:
                logger.error(f"Failed to create/update realm: {result.output.decode('utf-8')}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Failed to create/update realm: {e}")
            return False
    
    def create_clients(self, realm: str, clients_config: Dict[str, Any]) -> bool:
        """
        Create or update clients in a realm
        
        Args:
            realm: Realm name
            clients_config: Clients configuration
            
        Returns:
            bool: True if all clients were created successfully
        """
        try:
            clients = clients_config.get('clients', [])
            success = True
            
            for client in clients:
                logger.info(f"Creating/updating client: {client.get('clientId')} in realm {realm}")
                
                # Convert to JSON
                client_json = json.dumps(client)
                
                # Check if client exists
                check_result = self.keycloak_container.exec_run([
                    "/bin/bash", "-c", 
                    f"/opt/keycloak/bin/kcadm.sh get clients -r {realm} --fields id,clientId | grep {client.get('clientId')}"
                ])
                
                if check_result.exit_code == 0 and check_result.output:
                    # Extract client ID
                    try:
                        client_info = json.loads(check_result.output)
                        client_id = [c['id'] for c in client_info if c['clientId'] == client.get('clientId')][0]
                        
                        # Update existing client
                        result = self.keycloak_container.exec_run([
                            "/bin/bash", "-c", 
                            f"echo '{client_json}' | /opt/keycloak/bin/kcadm.sh update clients/{client_id} -r {realm}"
                        ])
                    except Exception as e:
                        logger.error(f"Failed to parse client ID: {e}")
                        success = False
                        continue
                else:
                    # Create new client
                    result = self.keycloak_container.exec_run([
                        "/bin/bash", "-c", 
                        f"echo '{client_json}' | /opt/keycloak/bin/kcadm.sh create clients -r {realm}"
                    ])
                    
                if result.exit_code != 0:
                    logger.error(f"Failed to create/update client {client.get('clientId')}: {result.output.decode('utf-8')}")
                    success = False
                
            return success
        except Exception as e:
            logger.error(f"Failed to create/update clients: {e}")
            return False
    
    def create_roles(self, realm: str, roles_config: Dict[str, Any]) -> bool:
        """
        Create or update roles in a realm
        
        Args:
            realm: Realm name
            roles_config: Roles configuration
            
        Returns:
            bool: True if all roles were created successfully
        """
        try:
            # Create realm roles
            realm_roles = roles_config.get('realmRoles', [])
            success = True
            
            for role in realm_roles:
                logger.info(f"Creating/updating realm role: {role.get('name')} in realm {realm}")
                
                # Remove composites from role definition for creation/update
                role_def = {k: v for k, v in role.items() if k != 'composites'}
                role_json = json.dumps(role_def)
                
                # Check if role exists
                check_result = self.keycloak_container.exec_run([
                    "/bin/bash", "-c", 
                    f"/opt/keycloak/bin/kcadm.sh get roles -r {realm} | grep {role.get('name')}"
                ])
                
                if check_result.exit_code == 0 and check_result.output:
                    # Update existing role
                    result = self.keycloak_container.exec_run([
                        "/bin/bash", "-c", 
                        f"echo '{role_json}' | /opt/keycloak/bin/kcadm.sh update roles/{role.get('name')} -r {realm}"
                    ])
                else:
                    # Create new role
                    result = self.keycloak_container.exec_run([
                        "/bin/bash", "-c", 
                        f"echo '{role_json}' | /opt/keycloak/bin/kcadm.sh create roles -r {realm}"
                    ])
                    
                if result.exit_code != 0:
                    logger.error(f"Failed to create/update role {role.get('name')}: {result.output.decode('utf-8')}")
                    success = False
                    
                # Add composites if defined
                if role.get('composite') and role.get('composites'):
                    composites = role.get('composites', {})
                    
                    # Realm role composites
                    realm_composites = composites.get('realm', [])
                    if realm_composites:
                        composite_json = json.dumps([{"id": r, "name": r} for r in realm_composites])
                        comp_result = self.keycloak_container.exec_run([
                            "/bin/bash", "-c", 
                            f"echo '{composite_json}' | /opt/keycloak/bin/kcadm.sh add-roles -r {realm} --rname {role.get('name')} --rolename {','.join(realm_composites)}"
                        ])
                        
                        if comp_result.exit_code != 0:
                            logger.error(f"Failed to add composites to role {role.get('name')}: {comp_result.output.decode('utf-8')}")
                            success = False
            
            # Create client roles
            client_roles = roles_config.get('clientRoles', [])
            
            for client_role_set in client_roles:
                client_id = client_role_set.get('clientId')
                roles = client_role_set.get('roles', [])
                
                # Get client UUID
                client_uuid_result = self.keycloak_container.exec_run([
                    "/bin/bash", "-c", 
                    f"/opt/keycloak/bin/kcadm.sh get clients -r {realm} --fields id,clientId | grep {client_id}"
                ])
                
                if client_uuid_result.exit_code != 0 or not client_uuid_result.output:
                    logger.error(f"Client {client_id} not found")
                    success = False
                    continue
                    
                try:
                    client_info = json.loads(client_uuid_result.output)
                    client_uuid = [c['id'] for c in client_info if c['clientId'] == client_id][0]
                    
                    for role in roles:
                        logger.info(f"Creating/updating client role: {role.get('name')} for client {client_id}")
                        
                        # Remove composites from role definition for creation/update
                        role_def = {k: v for k, v in role.items() if k != 'composites'}
                        role_json = json.dumps(role_def)
                        
                        # Check if role exists
                        check_result = self.keycloak_container.exec_run([
                            "/bin/bash", "-c", 
                            f"/opt/keycloak/bin/kcadm.sh get clients/{client_uuid}/roles -r {realm} | grep {role.get('name')}"
                        ])
                        
                        if check_result.exit_code == 0 and check_result.output:
                            # Update existing role
                            result = self.keycloak_container.exec_run([
                                "/bin/bash", "-c", 
                                f"echo '{role_json}' | /opt/keycloak/bin/kcadm.sh update clients/{client_uuid}/roles/{role.get('name')} -r {realm}"
                            ])
                        else:
                            # Create new role
                            result = self.keycloak_container.exec_run([
                                "/bin/bash", "-c", 
                                f"echo '{role_json}' | /opt/keycloak/bin/kcadm.sh create clients/{client_uuid}/roles -r {realm}"
                            ])
                            
                        if result.exit_code != 0:
                            logger.error(f"Failed to create/update client role {role.get('name')}: {result.output.decode('utf-8')}")
                            success = False
                except Exception as e:
                    logger.error(f"Failed to parse client ID: {e}")
                    success = False
                
            return success
        except Exception as e:
            logger.error(f"Failed to create/update roles: {e}")
            return False
    
    def create_authentication_flows(self, realm: str, auth_config: Dict[str, Any]) -> bool:
        """
        Create authentication flows in a realm
        
        Args:
            realm: Realm name
            auth_config: Authentication configuration
            
        Returns:
            bool: True if all flows were created successfully
        """
        try:
            flows = auth_config.get('authenticationFlows', [])
            success = True
            
            # First pass: create top-level flows
            for flow in flows:
                if flow.get('topLevel'):
                    logger.info(f"Creating authentication flow: {flow.get('alias')} in realm {realm}")
                    
                    # Check if flow exists
                    check_result = self.keycloak_container.exec_run([
                        "/bin/bash", "-c", 
                        f"/opt/keycloak/bin/kcadm.sh get authentication/flows -r {realm} | grep {flow.get('alias')}"
                    ])
                    
                    if check_result.exit_code == 0 and check_result.output:
                        # Delete existing flow
                        delete_result = self.keycloak_container.exec_run([
                            "/bin/bash", "-c", 
                            f"/opt/keycloak/bin/kcadm.sh delete authentication/flows/{flow.get('alias')} -r {realm}"
                        ])
                        
                        if delete_result.exit_code != 0:
                            logger.error(f"Failed to delete existing flow {flow.get('alias')}: {delete_result.output.decode('utf-8')}")
                            success = False
                            continue
                    
                    # Create flow
                    flow_json = json.dumps({
                        'alias': flow.get('alias'),
                        'description': flow.get('description', ''),
                        'providerId': flow.get('providerId', 'basic-flow'),
                        'topLevel': flow.get('topLevel', True),
                        'builtIn': flow.get('builtIn', False)
                    })
                    
                    result = self.keycloak_container.exec_run([
                        "/bin/bash", "-c", 
                        f"echo '{flow_json}' | /opt/keycloak/bin/kcadm.sh create authentication/flows -r {realm}"
                    ])
                    
                    if result.exit_code != 0:
                        logger.error(f"Failed to create flow {flow.get('alias')}: {result.output.decode('utf-8')}")
                        success = False
            
            # Second pass: create non-top-level flows
            for flow in flows:
                if not flow.get('topLevel'):
                    logger.info(f"Creating sub-flow: {flow.get('alias')} in realm {realm}")
                    
                    # Find parent flow
                    parent_found = False
                    for parent_flow in flows:
                        if parent_flow.get('topLevel'):
                            for execution in parent_flow.get('authenticationExecutions', []):
                                if execution.get('flowAlias') == flow.get('alias'):
                                    # Create sub-flow in parent
                                    flow_json = json.dumps({
                                        'alias': flow.get('alias'),
                                        'description': flow.get('description', ''),
                                        'provider': flow.get('providerId', 'basic-flow'),
                                        'type': 'basic-flow'
                                    })
                                    
                                    result = self.keycloak_container.exec_run([
                                        "/bin/bash", "-c", 
                                        f"echo '{flow_json}' | /opt/keycloak/bin/kcadm.sh create authentication/flows/{parent_flow.get('alias')}/executions/flow -r {realm}"
                                    ])
                                    
                                    if result.exit_code != 0:
                                        logger.error(f"Failed to create sub-flow {flow.get('alias')}: {result.output.decode('utf-8')}")
                                        success = False
                                    
                                    parent_found = True
                                    break
                        if parent_found:
                            break
                    
                    if not parent_found:
                        logger.error(f"Parent flow for sub-flow {flow.get('alias')} not found")
                        success = False
            
            # Third pass: add executions to flows
            for flow in flows:
                for execution in flow.get('authenticationExecutions', []):
                    # Skip sub-flows, they were already created
                    if 'flowAlias' in execution:
                        continue
                        
                    logger.info(f"Adding execution {execution.get('authenticator')} to flow {flow.get('alias')}")
                    
                    execution_json = json.dumps({
                        'provider': execution.get('authenticator')
                    })
                    
                    result = self.keycloak_container.exec_run([
                        "/bin/bash", "-c", 
                        f"echo '{execution_json}' | /opt/keycloak/bin/kcadm.sh create authentication/flows/{flow.get('alias')}/executions/execution -r {realm}"
                    ])
                    
                    if result.exit_code != 0:
                        logger.error(f"Failed to add execution {execution.get('authenticator')} to flow {flow.get('alias')}: {result.output.decode('utf-8')}")
                        success = False
            
            # Fourth pass: update execution requirements
            for flow in flows:
                # Get flow executions
                exec_result = self.keycloak_container.exec_run([
                    "/bin/bash", "-c", 
                    f"/opt/keycloak/bin/kcadm.sh get authentication/flows/{flow.get('alias')}/executions -r {realm}"
                ])
                
                if exec_result.exit_code != 0:
                    logger.error(f"Failed to get executions for flow {flow.get('alias')}: {exec_result.output.decode('utf-8')}")
                    success = False
                    continue
                    
                try:
                    executions = json.loads(exec_result.output)
                    
                    for execution in executions:
                        exec_alias = execution.get('authenticator') or execution.get('displayName')
                        
                        # Find matching execution in config
                        for config_exec in flow.get('authenticationExecutions', []):
                            config_alias = config_exec.get('authenticator') or config_exec.get('flowAlias')
                            
                            if exec_alias == config_alias:
                                # Update execution
                                update_json = json.dumps({
                                    'id': execution.get('id'),
                                    'requirement': config_exec.get('requirement', 'DISABLED')
                                })
                                
                                update_result = self.keycloak_container.exec_run([
                                    "/bin/bash", "-c", 
                                    f"echo '{update_json}' | /opt/keycloak/bin/kcadm.sh update authentication/executions/{execution.get('id')} -r {realm}"
                                ])
                                
                                if update_result.exit_code != 0:
                                    logger.error(f"Failed to update execution {exec_alias}: {update_result.output.decode('utf-8')}")
                                    success = False
                except Exception as e:
                    logger.error(f"Failed to parse executions JSON: {e}")
                    success = False
            
            # Finally, update authentication bindings
            if 'authenticationFlowBindings' in auth_config:
                bindings = auth_config.get('authenticationFlowBindings')
                bindings_json = json.dumps(bindings)
                
                result = self.keycloak_container.exec_run([
                    "/bin/bash", "-c", 
                    f"echo '{bindings_json}' | /opt/keycloak/bin/kcadm.sh update authentication/flow-bindings -r {realm}"
                ])
                
                if result.exit_code != 0:
                    logger.error(f"Failed to update authentication bindings: {result.output.decode('utf-8')}")
                    success = False
            
            return success
        except Exception as e:
            logger.error(f"Failed to create authentication flows: {e}")
            return False
    
    def apply_all_configs(self, realm_name: str, variables: Dict[str, str]) -> bool:
        """
        Apply all configuration templates to create a fully configured realm
        
        Args:
            realm_name: Name of the realm to create/update
            variables: Dictionary of variables to substitute in templates
            
        Returns:
            bool: True if all configurations were applied successfully
        """
        try:
            # Authenticate
            if not self.authenticate_to_keycloak():
                return False
            
            # 1. Create realm
            realm_config = self.load_template('realm', variables)
            if not realm_config:
                logger.error("Failed to load realm template")
                return False
                
            if not self.create_realm(realm_config):
                logger.error("Failed to create/update realm")
                return False
                
            # 2. Create clients
            clients_config = self.load_template('clients', variables)
            if clients_config:
                if not self.create_clients(realm_name, clients_config):
                    logger.warning("Failed to create/update some clients")
            
            # 3. Create roles
            roles_config = self.load_template('roles', variables)
            if roles_config:
                if not self.create_roles(realm_name, roles_config):
                    logger.warning("Failed to create/update some roles")
            
            # 4. Create authentication flows
            auth_config = self.load_template('authentication', variables)
            if auth_config:
                if not self.create_authentication_flows(realm_name, auth_config):
                    logger.warning("Failed to create/update some authentication flows")
            
            logger.info(f"Successfully applied configurations to realm {realm_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply configurations: {e}")
            return False