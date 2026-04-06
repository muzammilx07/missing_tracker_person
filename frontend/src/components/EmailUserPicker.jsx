"use client";

import { useEffect, useMemo, useState } from "react";
import api from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";

export default function EmailUserPicker({ selectedUsers, onSelectUser, onRemoveUser }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const selectedIds = useMemo(
    () => new Set((selectedUsers || []).map((item) => item.id)),
    [selectedUsers]
  );

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const response = await api.get(`/users/search?q=${encodeURIComponent(query.trim())}`);
        setResults(response.data.users || []);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  return (
    <div className="space-y-3">
      <Command>
        <CommandInput
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search family member by email"
        />
        <CommandList>
          {loading ? <CommandEmpty>Searching...</CommandEmpty> : null}
          {!loading && !results.length && query ? <CommandEmpty>No users found</CommandEmpty> : null}
          {results
            .filter((user) => !selectedIds.has(user.id))
            .map((user) => (
              <CommandItem
                key={user.id}
                onClick={() => {
                  onSelectUser(user);
                  setQuery("");
                  setResults([]);
                }}
              >
                <span className="font-medium text-slate-800">{user.name}</span>
                <span className="text-xs text-slate-500">{user.email}</span>
              </CommandItem>
            ))}
        </CommandList>
      </Command>

      <div className="flex flex-wrap gap-2">
        {(selectedUsers || []).map((user) => (
          <Badge key={user.id} variant="secondary" className="gap-2">
            {user.email}
            <Button
              variant="ghost"
              size="sm"
              className="h-5 px-1 text-white hover:bg-slate-700"
              onClick={() => onRemoveUser(user.id)}
            >
              x
            </Button>
          </Badge>
        ))}
      </div>
    </div>
  );
}
