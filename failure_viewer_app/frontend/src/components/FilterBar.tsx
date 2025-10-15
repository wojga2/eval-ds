import { useState } from 'react';
import { X } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface FilterBarProps {
  availableCodes: string[];
  selectedCodes: string[];
  onCodesChange: (codes: string[]) => void;
  passFailFilter: 'pass' | 'fail' | null;
  onPassFailChange: (filter: 'pass' | 'fail' | null) => void;
  totalCount: number;
}

export function FilterBar({
  availableCodes,
  selectedCodes,
  onCodesChange,
  passFailFilter,
  onPassFailChange,
  totalCount,
}: FilterBarProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);

  const filteredCodes = availableCodes.filter(
    (code) =>
      !selectedCodes.includes(code) &&
      code.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const addCode = (code: string) => {
    onCodesChange([...selectedCodes, code]);
    setSearchTerm('');
    setShowDropdown(false);
  };

  const removeCode = (code: string) => {
    onCodesChange(selectedCodes.filter((c) => c !== code));
  };

  return (
    <div className="sticky top-0 z-10 bg-background border-b p-4 space-y-4">
      <div className="flex flex-wrap items-center gap-4">
        {/* Pass/Fail Filter */}
        <div className="flex gap-2">
          <Button
            variant={passFailFilter === null ? 'default' : 'outline'}
            size="sm"
            onClick={() => onPassFailChange(null)}
          >
            All
          </Button>
          <Button
            variant={passFailFilter === 'pass' ? 'default' : 'outline'}
            size="sm"
            onClick={() => onPassFailChange('pass')}
          >
            Pass
          </Button>
          <Button
            variant={passFailFilter === 'fail' ? 'default' : 'outline'}
            size="sm"
            onClick={() => onPassFailChange('fail')}
          >
            Fail
          </Button>
        </div>

        {/* Code Search */}
        <div className="relative flex-1 min-w-[300px]">
          <input
            type="text"
            placeholder="Type to search axial codes..."
            className="w-full px-3 py-2 border rounded-md"
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setShowDropdown(true);
            }}
            onFocus={() => setShowDropdown(true)}
          />
          {showDropdown && filteredCodes.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white border rounded-md shadow-lg max-h-60 overflow-y-auto z-20">
              {filteredCodes.map((code) => (
                <div
                  key={code}
                  className="px-3 py-2 hover:bg-accent cursor-pointer"
                  onClick={() => addCode(code)}
                >
                  {code}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Total Count */}
        <div className="text-sm font-semibold">
          {totalCount} task{totalCount !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Selected Codes */}
      {selectedCodes.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {selectedCodes.map((code) => (
            <Badge
              key={code}
              variant="secondary"
              className="cursor-pointer hover:bg-secondary/80 px-3 py-1"
            >
              {code}
              <X
                className="ml-2 h-3 w-3"
                onClick={(e) => {
                  e.stopPropagation();
                  removeCode(code);
                }}
              />
            </Badge>
          ))}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onCodesChange([])}
          >
            Clear all
          </Button>
        </div>
      )}
    </div>
  );
}

