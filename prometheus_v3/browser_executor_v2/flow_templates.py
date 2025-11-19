"""
Flow Templates
Templates prontos de flows comuns para Comet
"""

from .comet_contract import CometFlow, CometAction, CometContract
from .browser_action_schema import ActionSchema, SelectorBuilder


class FlowTemplates:
    """
    Templates de flows prontos para uso
    """

    @staticmethod
    def login_flow(
        flow_id: str,
        url: str,
        username_selector: str,
        password_selector: str,
        submit_selector: str,
        username: str = "${USERNAME}",
        password: str = "${PASSWORD}"
    ) -> CometFlow:
        """
        Template de login genérico

        Args:
            flow_id: ID do flow
            url: URL da página de login
            username_selector: Seletor do campo username
            password_selector: Seletor do campo password
            submit_selector: Seletor do botão submit
            username: Username (pode ser variável)
            password: Password (pode ser variável)

        Returns:
            CometFlow configurado
        """
        flow = CometFlow(
            flow_id=flow_id,
            name="Generic Login Flow",
            description=f"Login flow for {url}",
            metadata={"template": "login", "url": url}
        )

        # Navegar para página
        flow.add_action(CometAction(
            action=ActionSchema.navigate(url),
            description="Navigate to login page",
            critical=True
        ))

        # Aguardar campo username
        flow.add_action(CometAction(
            action=ActionSchema.wait_for_element(username_selector, timeout=10000),
            description="Wait for username field",
            critical=True
        ))

        # Digitar username
        flow.add_action(CometAction(
            action=ActionSchema.type_text(username_selector, username),
            description="Enter username",
            critical=True
        ))

        # Digitar password
        flow.add_action(CometAction(
            action=ActionSchema.type_text(password_selector, password),
            description="Enter password",
            critical=True
        ))

        # Clicar em submit
        flow.add_action(CometAction(
            action=ActionSchema.click(submit_selector),
            description="Click submit button",
            critical=True,
            retry_on_fail=True
        ))

        # Aguardar navegação
        flow.add_action(CometAction(
            action=ActionSchema.wait(3000),
            description="Wait for login to complete"
        ))

        return flow

    @staticmethod
    def extract_data_flow(
        flow_id: str,
        url: str,
        data_selectors: dict[str, str]
    ) -> CometFlow:
        """
        Template de extração de dados

        Args:
            flow_id: ID do flow
            url: URL da página
            data_selectors: Dict {campo: seletor}

        Returns:
            CometFlow configurado
        """
        flow = CometFlow(
            flow_id=flow_id,
            name="Data Extraction Flow",
            description=f"Extract data from {url}",
            metadata={"template": "extract", "url": url, "fields": list(data_selectors.keys())}
        )

        # Navegar
        flow.add_action(CometAction(
            action=ActionSchema.navigate(url),
            description="Navigate to page",
            critical=True
        ))

        # Aguardar carregamento
        flow.add_action(CometAction(
            action=ActionSchema.wait(2000),
            description="Wait for page load"
        ))

        # Extrair cada campo
        for field_name, selector in data_selectors.items():
            flow.add_action(CometAction(
                action=ActionSchema.extract(selector),
                description=f"Extract {field_name}",
                critical=False,
                retry_on_fail=True
            ))

        return flow

    @staticmethod
    def form_fill_flow(
        flow_id: str,
        url: str,
        form_fields: dict[str, str],
        submit_selector: str
    ) -> CometFlow:
        """
        Template de preenchimento de formulário

        Args:
            flow_id: ID do flow
            url: URL da página
            form_fields: Dict {seletor: valor}
            submit_selector: Seletor do botão submit

        Returns:
            CometFlow configurado
        """
        flow = CometFlow(
            flow_id=flow_id,
            name="Form Fill Flow",
            description=f"Fill form at {url}",
            metadata={"template": "form_fill", "url": url}
        )

        # Navegar
        flow.add_action(CometAction(
            action=ActionSchema.navigate(url),
            description="Navigate to form page",
            critical=True
        ))

        # Aguardar formulário
        flow.add_action(CometAction(
            action=ActionSchema.wait(2000),
            description="Wait for form load"
        ))

        # Preencher cada campo
        for selector, value in form_fields.items():
            flow.add_action(CometAction(
                action=ActionSchema.type_text(selector, value, wait_after=500),
                description=f"Fill field {selector}",
                critical=False,
                retry_on_fail=True
            ))

        # Submit
        flow.add_action(CometAction(
            action=ActionSchema.click(submit_selector),
            description="Submit form",
            critical=True,
            retry_on_fail=True
        ))

        return flow

    @staticmethod
    def pagination_extract_flow(
        flow_id: str,
        url: str,
        item_selector: str,
        next_button_selector: str,
        max_pages: int = 10
    ) -> CometFlow:
        """
        Template de extração com paginação

        Args:
            flow_id: ID do flow
            url: URL inicial
            item_selector: Seletor dos itens
            next_button_selector: Seletor do botão "próximo"
            max_pages: Número máximo de páginas

        Returns:
            CometFlow configurado
        """
        flow = CometFlow(
            flow_id=flow_id,
            name="Pagination Extract Flow",
            description=f"Extract paginated data from {url}",
            metadata={
                "template": "pagination",
                "url": url,
                "max_pages": max_pages
            }
        )

        # Navegar
        flow.add_action(CometAction(
            action=ActionSchema.navigate(url),
            description="Navigate to first page",
            critical=True
        ))

        # Loop de paginação (simplificado - Comet precisa implementar loop)
        for page in range(max_pages):
            # Aguardar itens
            flow.add_action(CometAction(
                action=ActionSchema.wait_for_element(item_selector, timeout=10000),
                description=f"Wait for items on page {page + 1}"
            ))

            # Extrair itens
            flow.add_action(CometAction(
                action=ActionSchema.extract(item_selector),
                description=f"Extract items from page {page + 1}",
                retry_on_fail=True
            ))

            # Clicar próximo (se não for última página)
            if page < max_pages - 1:
                flow.add_action(CometAction(
                    action=ActionSchema.click(next_button_selector),
                    description=f"Go to page {page + 2}",
                    retry_on_fail=False  # Se falhar, acabou paginação
                ))

                flow.add_action(CometAction(
                    action=ActionSchema.wait(2000),
                    description="Wait for next page load"
                ))

        return flow

    @staticmethod
    def screenshot_flow(
        flow_id: str,
        url: str,
        screenshot_name: str = "screenshot.png",
        scroll_before: bool = True
    ) -> CometFlow:
        """
        Template de captura de screenshot

        Args:
            flow_id: ID do flow
            url: URL da página
            screenshot_name: Nome do arquivo
            scroll_before: Scroll até o final antes de capturar

        Returns:
            CometFlow configurado
        """
        flow = CometFlow(
            flow_id=flow_id,
            name="Screenshot Flow",
            description=f"Capture screenshot of {url}",
            metadata={"template": "screenshot", "url": url}
        )

        # Navegar
        flow.add_action(CometAction(
            action=ActionSchema.navigate(url),
            description="Navigate to page",
            critical=True
        ))

        # Aguardar carregamento
        flow.add_action(CometAction(
            action=ActionSchema.wait(3000),
            description="Wait for full page load"
        ))

        # Scroll (opcional)
        if scroll_before:
            flow.add_action(CometAction(
                action=ActionSchema.scroll("bottom"),
                description="Scroll to bottom"
            ))

            flow.add_action(CometAction(
                action=ActionSchema.wait(1000),
                description="Wait after scroll"
            ))

        # Capturar screenshot
        flow.add_action(CometAction(
            action=ActionSchema.screenshot(screenshot_name),
            description="Capture screenshot",
            critical=True
        ))

        return flow


# Exemplo de uso
if __name__ == "__main__":
    # Criar contrato manager
    contract = CometContract()

    # Criar flow de login
    login_flow = FlowTemplates.login_flow(
        flow_id="login_example",
        url="https://example.com/login",
        username_selector=SelectorBuilder.by_id("username"),
        password_selector=SelectorBuilder.by_id("password"),
        submit_selector=SelectorBuilder.button_with_text("Login")
    )

    # Salvar flow
    contract.save_flow(login_flow)
    print(f"Flow salvo: {login_flow.flow_id}")

    # Gerar JSON
    print("\nFlow JSON:")
    print(login_flow.to_json())
7️⃣ PROMPTS OFICIAIS
📁 Estrutura de Diretórios
prometheus/
├── prompts/
│   ├── integrity/
│   │   └── integrity_system_prompt.txt
│   ├── executor/
│   │   ├── comet_navigator_prompt.txt
│   │   └── executor_planning_prompt.txt
│   └── supervisor/
│       ├── supervisor_protector_prompt.txt
│       └── code_review_prompt.txt
