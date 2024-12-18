import rich
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from datetime import datetime
import itertools
import json
import os
from pathlib import Path

console = Console()
word_components = {
    'words': set(),
    'numbers': set(),
    'special_chars': set()
}
configurations = {
    'min_length': 4,
    'max_length': 16,
    'capitalize': False,
    'include_reverse': False
}
output_dir = Path('wordlists')

leet_map = {
    'a': ['4', '@'],
    'b': ['8'],
    'e': ['3'],
    'i': ['1', '!'],
    'l': ['1'],
    'o': ['0'],
    's': ['5', '$'],
    't': ['7']
}

def create_leet_variations(word):
    results = {word, word.upper(), word.lower(), word.capitalize()}
    word_chars = list(word.lower())
    
    for i, char in enumerate(word_chars):
        if char in leet_map:
            for replacement in leet_map[char]:
                temp = word_chars.copy()
                temp[i] = replacement
                results.add(''.join(temp))
                results.add(''.join(temp).upper())
                results.add(''.join(temp).capitalize())
                
    return {w for w in results if configurations['min_length'] <= len(w) <= configurations['max_length']}

def generate_wordlist():
    all_components = []
    for category, items in word_components.items():
        all_components.extend(items)
    
    if not all_components:
        console.print("No components to generate from!", style="red")
        return []
    
    base_word = next(iter(word_components['words'])) if word_components['words'] else "wordlist"
    settings_str = []
    if configurations['capitalize']:
        settings_str.append('cap')
    if configurations['include_reverse']:
        settings_str.append('rev')
    settings_suffix = f"_{'-'.join(settings_str)}" if settings_str else ""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_file = output_dir / f"{base_word}_min{configurations['min_length']}_max{configurations['max_length']}{settings_suffix}_{timestamp}.txt"
    
    generated_words = set()
    console.print("[bold green]Starting wordlist generation...[/bold green]")
    
    try:
        words = list(word_components['words'])
        numbers = list(word_components['numbers'])
        special_chars = list(word_components['special_chars'])

        for word in words:
            variations = create_leet_variations(word)
            generated_words.update(variations)
            
            if configurations['include_reverse']:
                for var in variations:
                    generated_words.add(var[::-1])

            for word2 in words:
                combo = word + word2
                if configurations['min_length'] <= len(combo) <= configurations['max_length']:
                    combo_variations = create_leet_variations(combo)
                    generated_words.update(combo_variations)
                    
                    if configurations['include_reverse']:
                        for var in combo_variations:
                            generated_words.add(var[::-1])

            if numbers:
                for num in numbers:
                    combos = [word + num, num + word]
                    for combo in combos:
                        if configurations['min_length'] <= len(combo) <= configurations['max_length']:
                            combo_variations = create_leet_variations(combo)
                            generated_words.update(combo_variations)

            if special_chars:
                for char in special_chars:
                    combos = [word + char, char + word]
                    for combo in combos:
                        if configurations['min_length'] <= len(combo) <= configurations['max_length']:
                            combo_variations = create_leet_variations(combo)
                            generated_words.update(combo_variations)

        with output_file.open('w') as f:
            for word in sorted(generated_words):
                f.write(f"{word}\n")

        console.print(f"\n[bold green]✓ Completed! Generated {len(generated_words)} combinations[/bold green]")
        console.print(f"[bold cyan]Saved to: {output_file}[/bold cyan]")
        
    except Exception as e:
        console.print(f"\n[bold red]Error during generation: {str(e)}[/bold red]")
        return []

    return list(generated_words)

def add_components():
    console.print("\n[bold]Add Components[/bold]")
    console.print("Enter 'x' to return to main menu")
    console.print("Enter 'c' to change category")
    console.print(f"Minimum length: {configurations['min_length']}, Maximum length: {configurations['max_length']}")
    
    category = Prompt.ask("Select category", choices=["words", "numbers", "special_chars"])
    added_components = []
    
    while True:
        console.print(f"\nCurrent category: [bold]{category}[/bold]")
        value = Prompt.ask(f"Enter {category} (x:exit, c:change category)")
        
        if value.lower() == 'x':
            return True if added_components else False
        elif value.lower() == 'c':
            category = Prompt.ask("Select new category", choices=["words", "numbers", "special_chars"])
            continue
            
        if value and value.strip():
            value = value.strip()
            if len(value) < configurations['min_length']:
                console.print(f"Error: Input must be at least {configurations['min_length']} characters long", style="red")
                continue
            if len(value) > configurations['max_length']:
                console.print(f"Error: Input cannot be longer than {configurations['max_length']} characters", style="red")
                continue
                
            word_components[category].add(value)
            added_components.append((category, value))
            console.print(f"Added '{value}' to {category}", style="green")
            view_components()

def remove_components():
    components_to_remove = []
    while True:
        view_components()
        console.print("\n[bold]Remove Components[/bold]")
        console.print("Enter 'x' to return to main menu")
        console.print("Enter 'c' to change category")
        
        category = Prompt.ask("Select category to remove from", choices=["words", "numbers", "special_chars"])
        
        while True:
            console.print(f"\nCurrent items in {category}:")
            for idx, item in enumerate(sorted(word_components[category]), 1):
                console.print(f"{idx}. {item}")
            
            value = Prompt.ask("\nEnter value or index to remove (x/c to exit/change category)")
            
            if value.lower() == 'x':
                return components_to_remove
            elif value.lower() == 'c':
                break
            
            try:
                if value.isdigit():
                    idx = int(value) - 1
                    items_list = sorted(word_components[category])
                    if 0 <= idx < len(items_list):
                        value = items_list[idx]
                    else:
                        console.print("Invalid index!", style="red")
                        continue
                        
                if value in word_components[category]:
                    word_components[category].remove(value)
                    components_to_remove.append((category, value))
                    console.print(f"Removed '{value}' from {category}", style="green")
                else:
                    console.print(f"'{value}' not found in {category}!", style="red")
                    
            except (ValueError, IndexError):
                console.print("Invalid input!", style="red")

def configure_settings():
    console.print("\n[bold]Generator Configuration[/bold]")
    while True:
        try:
            min_length = int(Prompt.ask("Minimum length", default=str(configurations['min_length'])))
            if min_length <= 0:
                console.print("Minimum length must be positive", style="red")
                continue
            break
        except ValueError:
            console.print("Please enter a valid number", style="red")
    
    while True:
        try:
            max_length = int(Prompt.ask("Maximum length", default=str(configurations['max_length'])))
            if max_length < min_length:
                console.print(f"Maximum length must be greater than minimum length ({min_length})", style="red")
                continue
            break
        except ValueError:
            console.print("Please enter a valid number", style="red")
    
    configurations['min_length'] = min_length
    configurations['max_length'] = max_length
    configurations['capitalize'] = Confirm.ask(
        "Include capitalized versions?", default=configurations['capitalize'])
    configurations['include_reverse'] = Confirm.ask(
        "Include reversed combinations?", default=configurations['include_reverse'])
    return configurations

def view_components(show_counts=True):
    if show_counts:
        total = sum(len(items) for items in word_components.values())
        console.print(f"\n[bold cyan]Total components: {total}[/bold cyan]")
    
    for category, items in word_components.items():
        console.print(f"\n[bold]{category.upper()}[/bold] ({len(items)} items)")
        if items:
            for item in sorted(items):
                console.print(f"  • {item}")
        else:
            console.print("  (empty)", style="dim")
    return dict(word_components)

def display_banner():
    banner = """
╔════════════════════════════════╗
║    Advanced Wordlist Generator ║
║     Security Research Tool     ║
╚════════════════════════════════╝
"""
    console.print(Panel(banner, style="bold blue", width=40, padding=(0, 0)))

def show_menu():
    menu = Table(show_header=True, header_style="bold magenta")
    menu.add_column("Option", style="cyan", width=6)
    menu.add_column("Description", style="green")
    
    menu.add_row("1", "Add Components (words/numbers/special chars)")
    menu.add_row("2", "Configure Generator Settings")
    menu.add_row("3", "View Current Components")
    menu.add_row("4", "Remove Components")
    menu.add_row("5", "Generate Wordlist")
    menu.add_row("6", "Save/Load Configuration")
    menu.add_row("x", "Exit")
    
    console.print(menu)

def save_configuration():
    config = {
        'word_components': {k: list(v) for k, v in word_components.items()},
        'configurations': configurations
    }
    config_file = output_dir / 'config.json'
    with config_file.open('w') as f:
        json.dump(config, f, indent=2)
    console.print("Configuration saved!", style="green")
    return str(config_file)

def load_configuration():
    config_file = output_dir / 'config.json'
    if config_file.exists():
        with config_file.open('r') as f:
            config = json.load(f)
            word_components.update({k: set(v) for k, v in config['word_components'].items()})
            configurations.update(config['configurations'])
        console.print("Configuration loaded!", style="green")
        return True
    else:
        console.print("No saved configuration found!", style="yellow")
        return False

def main():
    output_dir.mkdir(exist_ok=True)
    try:
        while True:
            display_banner()
            show_menu()
            choice = Prompt.ask("\nSelect option", choices=["1", "2", "3", "4", "5", "6", "x"])
            
            if choice == "1":
                add_components()
            elif choice == "2":
                configure_settings()
            elif choice == "3":
                view_components()
            elif choice == "4":
                remove_components()
            elif choice == "5":
                generate_wordlist()
            elif choice == "6":
                subchoice = Prompt.ask("Choose action", choices=["save", "load"])
                if subchoice == "save":
                    save_configuration()
                else:
                    load_configuration()
            elif choice.lower() == "x":
                console.print("\nGoodbye!", style="bold blue")
                break
            
            if choice != "x":
                Prompt.ask("\nPress Enter to continue")
                os.system('cls' if os.name == 'nt' else 'clear')
                
    except KeyboardInterrupt:
        console.print("\nOperation cancelled by user.", style="yellow")
    except Exception as e:
        console.print(f"\n[bold red]Error: {str(e)}")

if __name__ == "__main__":
    main()