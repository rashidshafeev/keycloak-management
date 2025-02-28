import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Generator, ContextManager
from contextlib import contextmanager

from ..core.base import BaseStep
from .summary import InstallationSummaryGenerator

logger = logging.getLogger(__name__)

class StepOrchestrator:
    """Orchestrates the execution of deployment steps"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the orchestrator
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.steps = []
        
    def add_step(self, step: BaseStep) -> None:
        """
        Add a step to the orchestration sequence
        
        Args:
            step: The deployment step to add
        """
        self.steps.append(step)
        
    @contextmanager
    def step_context(self, step: BaseStep):
        """
        Context manager for step execution with proper logging
        
        Args:
            step: The deployment step
        """
        logger.info(f"Starting step: {step.name}")
        try:
            yield step
            logger.info(f"Completed step: {step.name}")
        except Exception as e:
            logger.error(f"Step {step.name} failed: {str(e)}", exc_info=True)
            raise
    
    def execute(self) -> bool:
        """
        Execute all steps in sequence
        
        Returns:
            True if all steps were successful, False otherwise
        """
        for step in self.steps:
            try:
                with self.step_context(step):
                    if not step.execute():
                        logger.error(f"Step {step.name} failed, aborting deployment")
                        return False
            except Exception as e:
                logger.error(f"Error during step {step.name}: {str(e)}", exc_info=True)
                return False
                
        # Generate installation summary after successful deployment
        try:
            summary_generator = InstallationSummaryGenerator(self.config)
            if not summary_generator.generate():
                logger.error("Failed to generate installation summary")
                # Continue anyway as this is not a critical error
            
        except Exception as e:
            logger.error(f"Failed to generate installation summary: {str(e)}", exc_info=True)
            # Continue anyway as this is not a critical error
            
        return True